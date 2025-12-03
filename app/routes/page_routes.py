from flask import Blueprint, render_template, redirect, url_for, session, current_app, send_from_directory, flash, request
from app.utils.helper import validate_latlon

static_bp = Blueprint('pages', __name__)

@static_bp.route('/')
def index():
    """ Home page -> redirect to map """

    cfg = current_app.config["APP_CONFIG"]

    session.setdefault('coordinates', [])
    session.setdefault('map_center',{
        'lat': cfg.map_default['lat'],
        'lon': cfg.map_default['lon']
    })
    
    return redirect(url_for('pages.map_view'))


@static_bp.route('/map')
def map_view():
    ''' Renders the map view with stored coordinates and center '''
    cfg = current_app.config["APP_CONFIG"]

    # Get coordinates and map center from session
    coords = session.get('coordinates', [])
    center = session.get('map_center', {
        'lat': cfg.map_default['lat'], 
        'lon': cfg.map_default['lon']
    })

    return render_template("map.html",
                           coordinates=coords,
                           map_center=center,
                           zoom=cfg.map_default['zoom'])


@static_bp.route('/search_location', methods=['POST'])
def search_location():
    ''' Handles location search and updates map center '''
    try:
        # Validate and extract latitude and longitude from form
        lat, lon = validate_latlon(request.form['latitude'], request.form['longitude'])

        # Update session with new map center
        session['map_center'] = {"lat": lat, "lon": lon}
        session.modified = True

        # Provide user feedback
        flash('Map centered on searched location.', 'success')
    except (ValueError, KeyError):
        flash('Invalid coordinates provided for search.', 'error')

    return redirect(url_for('pages.map_view'))


