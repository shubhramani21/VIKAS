from flask import session
from app.utils.helper import is_ajax, get_response, validate_latlon, coordinates_match

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
            return get_response("Invalid coordinates. Please enter valid numbers.", "error", 400, is_ajax(request)
                                )
    
        if len(coordinates) >= CoordinateController.MAX_LIMIT:
            return get_response(f"Maximum {CoordinateController.MAX_LIMIT} coordinates allowed.", "error", 400, is_ajax(request))
        
        
        if any(coordinates_match(c, lat, lon) for c in coordinates):
            return get_response("Coordinate already exists.", "warning", 400, is_ajax(request))
            

        coordinates.append({"lat": lat, "lon": lon})
        session["coordinates"] = coordinates
        session["map_center"] = {"lat": lat, "lon": lon}
        session.modified = True

        return get_response("Coordinate added successfully!", "success", 200, is_ajax(request))

    @staticmethod
    def delete_coordinate(lat, lon):
        """Delete coordinate by lat/lon"""
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return get_response("Invalid coordinates.", "error", 400)

        coords = session.get("coordinates", [])
        new_list = [c for c in coords if not coordinates_match((c["lat"], c["lon"]), lat, lon)]

        session["coordinates"] = new_list
        session.modified = True
        
        return get_response("Coordinate deleted successfully!", "success", 200, extra={"coordinates": new_list})

    @staticmethod
    def clear_all(request):
        """Clear all coordinates"""

        session["coordinates"] = []
        session.modified = True

        return get_response("All coordinates cleared!", "success", 200, is_ajax(request),
                            extra={"coordinates": []})


    @staticmethod
    def upload_coordinates(file_obj, request):
        """Upload coordinates from a CSV file."""
        if file_obj.filename == "None":
            return get_response("No file selected.", "error", 400, is_ajax(request))
        
        if not file_obj.filename.endswith(".csv"):
            return get_response("Invalid file format. Please upload a CSV file.", "error", 400, is_ajax(request))
        
        try:
            df = pd.read_csv(file_obj)
        except Exception as e:
            return get_response(f"Error reading CSV: {str(e)}", "error", 500, is_ajax(request))

        # Require Columns
        if not {"latitude", "longitude"}.issubset(df.columns):
            return get_response("CSV must contain 'latitude' and 'longitude' columns.", "error", 400, is_ajax(request))
        

        # Freah Start
        coordinates = []
        new_count = 0
        invalid_count = 0
        duplicates_count = 0

        for _, row in df.iterrows():
            try:
                lat, lon = validate_latlon(row["latitude"], row["longitude"])
            except ValueError:
                invalid_count += 1
                continue

            #Limit Check
            if len(coordinates) >+ CoordinateController.MAX_LIMIT:
                break


            # duplicate check 
            if any(coordinates_match((c["lat"], c["lon"]), lat, lon) for c in coordinates):
                duplicates_count += 1
                continue

            coordinates.append({"lat": lat, "lon": lon})
            new_count += 1


        session["coordinates"] = coordinates
        session.modified = True
        
        msg = f"Successfully added {new_count} new coordinates. {invalid_count} invalid coordinates ignored. {duplicates_count} duplicates ignored."

        return get_response(msg, "success", 200, is_ajax(request), extra={"coordinates": coordinates})
