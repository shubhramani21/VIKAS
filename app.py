import sys
import os
import time

from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify, send_file, send_from_directory
import pandas as pd
from config import Config
from model import SolarModel, load_model
from utils import get_image, predict_image, save_prediction
from datetime import datetime
from PIL import Image
import numpy as np

def resource_path(relative_path):
    """Get absolute path to resources for both dev and packaged mode"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

app = Flask(__name__,
            template_folder=resource_path('templates'),
            static_folder=resource_path('static'))
app.secret_key = os.urandom(24)  # Secure key for sessions and flash messages

images_dir = resource_path(os.path.join('static', 'images'))
os.makedirs(images_dir, exist_ok=True)  

def cleanup_old_images(max_age_hours=24):
    """Delete images in static/images/ older than max_age_hours."""
    try:
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        deleted_count = 0
        for filename in os.listdir(images_dir):
            file_path = os.path.join(images_dir, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    deleted_count += 1
        if deleted_count > 0:
            print(f"Cleaned up {deleted_count} old images from {images_dir}")
        return deleted_count
    except Exception as e:
        print(f"Error cleaning up images: {str(e)}")
        return 0

# Load configuration and model
cfg = Config()
model = load_model(cfg)

if model is None:
    @app.route('/')
    def index():
        return "Error: Model could not be loaded."
else:
    @app.route('/')
    def index():
        # Initialize session variables
        if 'coordinates' not in session:
            session['coordinates'] = []
        if 'map_center' not in session:
            session['map_center'] = {'lat': cfg.map_default['lat'], 'lon': cfg.map_default['lon']}
        return redirect(url_for('map'))
    
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory(resource_path('static'), filename)

    @app.route('/map')
    def map():
        """Render the map page with satellite imagery and coordinates table."""
        coordinates = session.get('coordinates', [])
        map_center = session.get('map_center', {'lat': cfg.map_default['lat'], 'lon': cfg.map_default['lon']})
        return render_template(
            'map.html',
            coordinates=[{'lat': c[0], 'lon': c[1]} for c in coordinates],
            map_center=map_center,
            zoom=cfg.map_default['zoom']
        )

    @app.route('/search_location', methods=['POST'])
    def search_location():
        """Handle Nominatim search, update map center."""
        try:
            lat = float(request.form['lat'])
            lon = float(request.form['lon'])
            session['map_center'] = {'lat': lat, 'lon': lon}
            session.modified = True
            flash('Map centered on searched location.', 'success')
        except ValueError:
            flash('Invalid search result.', 'error')
        return redirect(url_for('map'))

    @app.route('/add_coordinate', methods=['POST'])
    def add_coordinate():
        """Add a coordinate to the session."""
        try:
            lat = float(request.form['lat'])
            lon = float(request.form['lon'])
            coordinates = session.get('coordinates', [])
            if not any(abs(c[0] - lat) < 0.0001 and abs(c[1] - lon) < 0.0001 for c in coordinates):
                coordinates.append([lat, lon])
                session['coordinates'] = coordinates
                # Update map center to the new coordinate
                session['map_center'] = {'lat': lat, 'lon': lon}
                session.modified = True
                # Return JSON for AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'status': 'success',
                        'message': 'Coordinate added successfully!',
                        'lat': lat,
                        'lon': lon
                    })
                flash(f'Coordinate added! Lat: {lat:.6f}, Lon: {lon:.6f}', 'success')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'status': 'warning',
                        'message': 'Coordinate already exists.'
                    }), 400
                flash('Coordinate already exists.', 'warning')
        except ValueError:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid coordinates. Please enter valid numbers.'
                }), 400
            flash('Invalid coordinates. Please enter valid numbers.', 'error')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'Unknown error.'}), 500
        return redirect(url_for('map'))

    @app.route('/predict_coordinate', methods=['POST'])
    def predict_coordinate():
        """Predict solar panel presence for a coordinate."""
        try:
            lat = float(request.form['lat'])
            lon = float(request.form['lon'])
            # Update map center to the predicted coordinate
            session['map_center'] = {'lat': lat, 'lon': lon}
            # Remove from session coordinates
            coordinates = session.get('coordinates', [])
            session['coordinates'] = [c for c in coordinates if not (abs(c[0]-lat) < 0.0001 and abs(c[1]-lon) < 0.0001)]
            session.modified = True

            image = get_image(lat, lon, zoom=cfg.zoom_level)
            if image is None:
                flash('Failed to fetch satellite image.', 'error')
                return render_template('prediction.html', lat=lat, lon=lon)
            print(f"Image type from get_image: {type(image)}")  # Debug
            # Ensure image is a numpy array for predict_image
            if not isinstance(image, np.ndarray):
                flash('Unsupported image format from get_image.', 'error')
                return render_template('prediction.html', lat=lat, lon=lon)
            # Save a copy as PIL Image for display
            image_pil = Image.fromarray(image.astype('uint8'))
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            image_filename = f'image_{timestamp}.jpg'
            image_path = os.path.join(images_dir, image_filename)
            image_pil.save(image_path, 'JPEG')
            print(f"Image saved: {image_path}")  # Debug
            # Clean up old images
            cleanup_old_images(max_age_hours=24)
            # Use original numpy array for prediction
            label, confidence = predict_image(image, model)
            save_prediction(lat, lon, label, confidence, cfg.predictions_file)
            flash('Prediction successful!', 'success')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'success',
                    'message': 'Prediction completed',
                    'image_filename': image_filename
                })
            return render_template(
                'prediction.html',
                show_sidebar=False,
                label=label,
                confidence=confidence,
                lat=lat,
                lon=lon,
                image_filename=image_filename
            )
        except ValueError:
            flash('Invalid coordinates.', 'error')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
            flash(f'Prediction error: {str(e)}', 'error')
        return redirect(url_for('map'))

    @app.route('/delete_coordinate', methods=['POST'])
    def delete_coordinate():
        """Delete a coordinate from the session."""
        try:
            lat = float(request.form['lat'])
            lon = float(request.form['lon'])
            coordinates = session.get('coordinates', [])
            coordinates = [c for c in coordinates if not (abs(c[0] - lat) < 0.0001 and abs(c[1] - lon) < 0.0001)]
            session['coordinates'] = coordinates
            session.modified = True
            flash('Coordinate deleted successfully!', 'success')
        except ValueError:
            flash('Invalid coordinates.', 'error')
        return redirect(url_for('map'))

    @app.route('/prediction', methods=['GET', 'POST'])
    def prediction():
        """Handle manual predictions."""
        if request.method == 'POST':
            try:
                lat = float(request.form['lat'])
                lon = float(request.form['lon'])
                
                # Remove coordinate from session BEFORE processing
                coordinates = session.get('coordinates', [])
                session['coordinates'] = [
                    c for c in coordinates 
                    if not (abs(c[0]-lat) < 0.0001 and abs(c[1]-lon) < 0.0001)
                ]
                session.modified = True

                image = get_image(lat, lon, zoom=cfg.zoom_level)
                if image is None:
                    flash('Failed to fetch satellite image.', 'error')
                    return render_template('prediction.html', lat=lat, lon=lon)
                print(f"Image type from get_image: {type(image)}")  # Debug
                # Ensure image is a numpy array for predict_image
                if not isinstance(image, np.ndarray):
                    flash('Unsupported image format from get_image.', 'error')
                    return render_template('prediction.html', lat=lat, lon=lon)
                # Save a copy as PIL Image for display
                image_pil = Image.fromarray(image.astype('uint8'))
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                image_filename = f'image_{timestamp}.jpg'
                image_path = os.path.join(images_dir, image_filename)
                image_pil.save(image_path, 'JPEG')
                print(f"Image saved: {image_path}")  # Debug
                # Clean up old images
                cleanup_old_images(max_age_hours=24)
                # Use original numpy array for prediction
                label, confidence = predict_image(image, model)
                save_prediction(lat, lon, label, confidence, cfg.predictions_file)
                flash('Prediction successful!', 'success')
                return render_template(
                    'prediction.html',
                    show_sidebar=False,
                    label=label,
                    confidence=confidence,
                    lat=lat,
                    lon=lon,
                    image_filename=image_filename
                )
            except ValueError:
                flash('Invalid coordinates.', 'error')
            except Exception as e:
                flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('map'))  # Fallback to working route

    @app.route('/predictions')
    def predictions():
        """Display prediction history."""
        try:
            df = pd.read_csv(cfg.predictions_file)
            print(f"CSV loaded: {df}")  # Debug: Log CSV content
            # Convert column names to lowercase
            df.columns = df.columns.str.lower()
            # Define required columns
            required_columns = ['latitude', 'longitude', 'label', 'confidence', 'timestamp']
            if not all(col in df.columns for col in required_columns):
                print(f"Missing columns: {set(required_columns) - set(df.columns)}")  # Debug
                flash('Invalid predictions file format.', 'error')
                return render_template('predictions.html', predictions=[])
            # Drop rows with missing or non-numeric latitude/longitude
            df = df.dropna(subset=required_columns)
            df = df[pd.to_numeric(df['latitude'], errors='coerce').notnull()]
            df = df[pd.to_numeric(df['longitude'], errors='coerce').notnull()]
            predictions_list = df.to_dict('records')
            print(f"Filtered predictions: {predictions_list}")  # Debug
            if not predictions_list:
                flash('No valid predictions found.', 'warning')
        except FileNotFoundError:
            print(f"File not found: {cfg.predictions_file}")  # Debug
            predictions_list = []
            flash('No predictions file found.', 'warning')
        except Exception as e:
            print(f"Error reading predictions: {str(e)}")  # Debug
            predictions_list = []
            flash(f'Error reading predictions: {str(e)}', 'error')
        return render_template('predictions.html',  show_sidebar=False, predictions=predictions_list)

    @app.route('/predict_all', methods=['POST'])
    def predict_all():
        """Predict solar panel presence for all coordinates with a 2-second delay."""
        try:
            predictions = []
            coordinates = session.get('coordinates', [])
            
            for idx, coord in enumerate(coordinates):
                lat = coord[0]
                lon = coord[1]
                
                # Get and process image
                image = get_image(lat, lon, zoom=cfg.zoom_level)
                if not isinstance(image, np.ndarray):
                    continue  # Skip invalid images
                
                # Save image
                image_pil = Image.fromarray(image.astype('uint8'))
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                image_filename = f'batch_{timestamp}_{idx}.jpg'  # Unique filename
                image_path = os.path.join(images_dir, image_filename)
                image_pil.save(image_path, 'JPEG')
                
                # Make prediction
                label, confidence = predict_image(image, model)
                
                # Save to predictions file
                save_prediction(
                    lat=lat,
                    lon=lon,
                    label=label,
                    confidence=confidence,
                    file_path=cfg.predictions_file
                )
                
                predictions.append({
                    'lat': lat,
                    'lon': lon,
                    'label': label,
                    'confidence': confidence,
                    'image_filename': image_filename
                })
                
                # Add 2-second delay to respect API rate limits
                time.sleep(2)
            
            # Clear coordinates after successful predictions
            session['coordinates'] = []
            session.modified = True
            cleanup_old_images(max_age_hours=24)
            
            return render_template('predict_all.html', show_sidebar=False, predictions=predictions)
    
        except Exception as e:
            flash(f'Batch prediction failed: {str(e)}', 'error')
            return redirect(url_for('map'))

    @app.route('/download_predictions')
    def download_predictions():
        """Download the predictions CSV file."""
        csv_path = resource_path(cfg.predictions_file)
        if not os.path.exists(csv_path):
            flash('No predictions file found to download', 'error')
            return redirect(url_for('predictions'))
            
        return send_file(
            csv_path,
            mimetype='text/csv',
            download_name='solar_predictions.csv',
            as_attachment=True
        )

    @app.route('/clear_predictions', methods=['POST'])
    def clear_predictions():
        """Clear all prediction history."""
        try:
            if not os.path.exists(cfg.predictions_file):
                flash('No predictions found to clear', 'error')
                return redirect(url_for('predictions'))
                
            os.remove(cfg.predictions_file)
            flash('All prediction history has been cleared', 'success')
        except Exception as e:
            flash(f'Error clearing predictions: {str(e)}', 'error')
        return redirect(url_for('predictions'))

if __name__ == '__main__':
    app.run(debug=True)