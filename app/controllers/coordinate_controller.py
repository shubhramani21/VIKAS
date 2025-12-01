from flask import session
from app.utils.helper import is_ajax, get_response, validate_latlon, coordinates_match, validate_latlon

import pandas as pd


class CoordinateController:
    MAX_LIMIT = 30

    @staticmethod
    def add_coordinate(lat, lon, coordinates, request):
        """Add a coordinate to the session."""

        # Validate
        try:
            lat, lon = validate_latlon(lat, lon)

        except ValueError:
            return get_response("Invalid coordinates. Please enter valid numbers.", "error", 400)
    
        if len(coordinates) >= CoordinateController.MAX_LIMIT:
            if is_ajax(request):
                return get_response("Maximum 30 coordinates allowed.", "error", 400, True)
        
        if any(coordinates_match(c, lat, lon) for c in coordinates):
            if is_ajax(request):
                return get_response("Coordinate already exists.", "warning", 400, True)
            

        coordinates.append([lat, lon])
        session["coordinates"] = coordinates
        session["map_center"] = {"lat": lat, "lon": lon}
        session.modified = True

        if is_ajax(request):
            return get_response("Coordinate added successfully!", "success", 200, True)
        
        return get_response("Coordinate added successfully!", "success", 200)

    @staticmethod
    def delete_coordinate(lat, lon):
        """Delete coordinate by lat/lon"""
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return get_response("Invalid coordinates. Please enter valid numbers.", "error", 400)

        coordinates = session.get("coordinates", [])
        session["coordinates"] = [ c for c in coordinates if not coordinates_match(c, lat, lon) ]
        session.modified = True
        
        return get_response("Coordinate deleted successfully!", "success", 200) 

    @staticmethod
    def clear_all(request):
        """Clear all coordinates"""
        try:

            session["coordinates"] = []
            session.modified = True

            if is_ajax(request):
                return get_response("All coordinates have been cleared successfully!", "success", 200, True)
        

            return get_response(
                "All coordinates cleared!",
                "success",
                200
            )
        except Exception as e:
            if is_ajax(request):
                return get_response(f"Error clearing coordinates: {str(e)}", "error", 500, True)
            
            return get_response(f"Error clearing coordinates: {str(e)}", "error", 500)  

    @staticmethod
    def upload_coordinates(file_name):
        """Upload coordinates from a CSV file."""
        if file_name.filename == "":
            return get_response("No file selected.", "error", 400)
        
        if file_name and file_name.filename.endwith(".csv"):
            try:
                session["coordinates"] = []
                session.modified = True

                df = pd.read_csv(file_name)
                required_columns = ["latitude", "longitude"]
                if not all(col in df.columns for col in required_columns):
                    return get_response("CSV must contain 'latitude' and 'longitude' columns.", "error", 400)
                

                coordinates = []
                new_coords = 0
                invalid_coords = 0  

                for _, row in df.iterrows():
                    try:
                        lat, lon = validate_latlon(row["latitude"], row["longitude"])
                        # Check for duplicates 
                        if not any(coordinates_match(c, lat, lon) for c in coordinates):

                            if len(coordinates) > CoordinateController.MAX_LIMIT:
                                return get_response(f"Maximum {CoordinateController.MAX_LIMIT} coordinates allowed.", "error", 400)
                            
                            coordinates.append([lat, lon])
                            new_coords += 1
                        else:
                            return get_response("Some coordinates were duplicates and ignored.", "warning", 400)
                    except ValueError:
                        invalid_coords += 1
                        continue
                
                session["coordinates"] = coordinates
                session.modified = True
                return get_response(f"Successfully added {new_coords} new coordinates. {invalid_coords} invalid coordinates ignored.", "success", 200)
            
            except Exception as e:
                return get_response(f"Error processing CSV: {str(e)}", "error", 500)
            
        else:
            return get_response("Invalid file format. Please upload a CSV file.", "error", 400)
        


                

                



