import math
import requests
import logging
from typing import List, Dict, Tuple
from google.adk.tools.tool_context import ToolContext
import google.auth
import google.auth.transport.requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("route_planner_tools")

def set_trip_details(start_location: str, end_location: str, start_time: str, tool_context: ToolContext) -> dict:
    """Saves the trip start/end locations and start time to the session state.

    Args:
        start_location (str): Starting location address.
        end_location (str): Ending location address.
        start_time (str): Chosen start time (e.g., "09:00" or "09:00 AM", must be between 7:00 AM and 11:00 AM).

    Returns:
        dict: Success or error status message.
    """
    logger.info(f"Setting trip details: Start='{start_location}', End='{end_location}', Time='{start_time}'")
    
    # Validate start/end locations are not URLs or domain strings (handling browser autofill / metadata pollution)
    invalid_keywords = ["http://", "https://", "vertexaisearch", "localhost:", "cloud.google.com"]
    if any(k in start_location.lower() for k in invalid_keywords):
        return {
            "status": "error",
            "message": "Starting Address cannot be a URL or domain. Please enter a valid street address."
        }
    if any(k in end_location.lower() for k in invalid_keywords):
        return {
            "status": "error",
            "message": "Ending Address cannot be a URL or domain. Please enter a valid street address."
        }

    # Simple validation of start time
    clean_time = start_time.upper().replace(" ", "")
    # Check if time format is valid
    try:
        # Extract hour
        if ":" in clean_time:
            hour_part = clean_time.split(":")[0]
            # Strip non-numeric
            hour_val = int("".join(c for c in hour_part if c.isdigit()))
            
            # Check if PM is in the time
            is_pm = "PM" in clean_time
            if is_pm and hour_val < 12:
                hour_val += 12
            elif not is_pm and hour_val == 12: # 12 AM
                hour_val = 0
                
            if hour_val < 7 or hour_val > 11:
                if not (7 <= hour_val <= 11) and not (12 <= hour_val <= 23): # Handle 24h
                    # If 24h format
                    if not (7 <= hour_val <= 11):
                        return {
                            "status": "error", 
                            "message": f"Start time '{start_time}' is outside the allowed range of 7:00 AM to 11:00 AM."
                        }
        else:
            return {"status": "error", "message": "Invalid time format. Please specify as HH:MM."}
    except Exception as e:
        logger.warning(f"Error parsing start time: {str(e)}")
        
    tool_context.state["start_location"] = start_location
    tool_context.state["end_location"] = end_location
    tool_context.state["start_time"] = start_time
    
    return {"status": "success", "message": "Trip details saved successfully."}

def fetch_service_requests(tool_context: ToolContext) -> dict:
    """Fetches the daily service requests assigned to the field representative.

    Returns:
        dict: A dictionary containing a list of service requests. Each request 
              contains a request_number, customer_name, and customer_address.
    """
    logger.info("Fetching service requests...")
    requests_list = [
        {
            "request_number": "SR-101",
            "customer_name": "Alice Johnson",
            "customer_address": "675 Ponce De Leon Ave NE, Atlanta, GA 30308"
        },
        {
            "request_number": "SR-102",
            "customer_name": "Bob Smith",
            "customer_address": "101 E Court Square, Decatur, GA 30030"
        },
        {
            "request_number": "SR-103",
            "customer_name": "Charlie Brown",
            "customer_address": "4400 Ashford Dunwoody Rd, Atlanta, GA 30346"
        },
        {
            "request_number": "SR-104",
            "customer_name": "Diana Prince",
            "customer_address": "99 E Park Square, Marietta, GA 30060"
        },
        {
            "request_number": "SR-105",
            "customer_name": "Evan Wright",
            "customer_address": "2200 Avalon Blvd, Alpharetta, GA 30009"
        },
        {
            "request_number": "SR-106",
            "customer_name": "Fiona Gallagher",
            "customer_address": "1978 Island Ford Pkwy, Sandy Springs, GA 30350"
        },
        {
            "request_number": "SR-107",
            "customer_name": "George Clark",
            "customer_address": "225 Baker St NW, Atlanta, GA 30313"
        }
    ]
    
    # Save to state
    tool_context.state["service_requests"] = requests_list
    return {"service_requests": requests_list}

def _haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Calculates geodesic distance in meters using Haversine formula."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371000  # radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def geocode_address(address: str, access_token: str = None, project: str = None) -> Tuple[float, float]:
    """Geocodes an address to (latitude, longitude) using offline known locations or the Address Validation API."""
    logger.info(f"Geocoding address: '{address}'")
    
    if not access_token or not project:
        try:
            credentials, project = google.auth.default(
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            auth_req = google.auth.transport.requests.Request()
            credentials.refresh(auth_req)
            access_token = credentials.token
        except Exception as e:
            logger.warning(f"Failed to automatically obtain credentials in geocode_address: {str(e)}")

    if not access_token or not project:
        logger.warning(f"No credentials available for real-time geocoding of '{address}'. Using default Atlanta coordinate.")
        return (33.7490, -84.3880)
        
    url = "https://addressvalidation.googleapis.com/v1:validateAddress"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Goog-User-Project": project,
        "Content-Type": "application/json"
    }
    body = {
        "address": {
            "addressLines": [address]
        }
    }
    try:
        response = requests.post(url, headers=headers, json=body, timeout=4)
        if response.status_code == 200:
            result = response.json()
            geocode = result.get("result", {}).get("geocode", {})
            location = geocode.get("location", {})
            lat = location.get("latitude")
            lng = location.get("longitude")
            if lat is not None and lng is not None:
                logger.info(f"Successfully geocoded '{address}' to ({lat}, {lng})")
                return (lat, lng)
            else:
                raise ValueError("Geocoding result did not contain coordinates.")
        else:
            raise ValueError(f"Address Validation API status {response.status_code}")
    except Exception as e:
        logger.warning(f"Failed to query Address Validation API for '{address}': {str(e)}. Using default Atlanta coordinate.")
        
    return (33.7490, -84.3880)

def _get_fallback_travel_matrix(origins: List[str], destinations: List[str], access_token: str = None, project: str = None) -> dict:
    """Calculates fallback distance/duration matrix using geocoded coordinates."""
    logger.info("Computing fallback travel matrix using geodesic estimations...")
    matrix = []
    
    # Pre-geocode all locations to optimize performance
    coords = []
    for addr in origins:
        c = geocode_address(addr, access_token, project)
        coords.append(c)
        
    for i, origin in enumerate(origins):
        row = {"elements": []}
        coord1 = coords[i]
        for j, dest in enumerate(destinations):
            if origin.lower().strip() == dest.lower().strip():
                dist_meters = 0.0
                duration_seconds = 0.0
            else:
                if len(origins) == len(destinations) and origins == destinations:
                    coord2 = coords[j]
                else:
                    coord2 = geocode_address(dest, access_token, project)
                
                dist_meters = _haversine_distance(coord1, coord2)
                duration_seconds = dist_meters / 13.4
                
            row["elements"].append({
                "status": "OK",
                "distance": {"value": int(dist_meters)},
                "duration": {"value": int(duration_seconds)}
            })
        matrix.append(row)
        
    return {"rows": matrix}

def get_travel_matrix(tool_context: ToolContext) -> dict:
    """Queries the Google Maps Routes API to retrieve travel durations and distances.

    Constructs the coordinates list directly using start_location, end_location, and
    service_requests stored in the session state.

    Returns:
        dict: A dictionary containing travel rows and matrix elements.
    """
    # Read from session state
    start_location = tool_context.state.get("start_location")
    end_location = tool_context.state.get("end_location")
    service_requests = tool_context.state.get("service_requests", [])
    
    if not start_location or not end_location:
        raise ValueError("start_location and end_location must be set in session state before calling get_travel_matrix.")
        
    # Consolidate unique addresses list: start + requests + end
    origins = [start_location] + [r["customer_address"] for r in service_requests] + [end_location]
    destinations = list(origins)
    
    logger.info(f"Requesting travel matrix for {len(origins)} locations from session state.")
    access_token = None
    project = None
    
    try:
        credentials, project = google.auth.default(
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        access_token = credentials.token
        
        url = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Goog-User-Project": project,
            "Content-Type": "application/json",
            "X-Goog-FieldMask": "originIndex,destinationIndex,status,duration,distanceMeters"
        }
        
        body = {
            "origins": [{"waypoint": {"address": addr}} for addr in origins],
            "destinations": [{"waypoint": {"address": addr}} for addr in destinations],
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE"
        }
        
        response = requests.post(url, headers=headers, json=body, timeout=10)
        
        if response.status_code == 200:
            results = response.json()
            logger.info("Successfully fetched route matrix from Google Routes API.")
            
            rows = [{"elements": [None] * len(destinations)} for _ in range(len(origins))]
            
            for item in results:
                o_idx = item.get("originIndex", 0)
                d_idx = item.get("destinationIndex", 0)
                
                status_obj = item.get("status", {})
                status_code = status_obj.get("code", 0)
                status_str = "OK" if status_code == 0 else "ERROR"
                
                duration_str = item.get("duration", "0s")
                if duration_str.endswith("s"):
                    duration_val = int(float(duration_str[:-1]))
                else:
                    duration_val = int(duration_str)
                    
                dist_val = item.get("distanceMeters", 0)
                
                rows[o_idx]["elements"][d_idx] = {
                    "status": status_str,
                    "distance": {"value": dist_val},
                    "duration": {"value": duration_val}
                }
                
            for r in range(len(origins)):
                for c in range(len(destinations)):
                    if rows[r]["elements"][c] is None:
                        rows[r]["elements"][c] = {
                            "status": "OK",
                            "distance": {"value": 0},
                            "duration": {"value": 0}
                        }
            
            # Save to state
            tool_context.state["travel_matrix"] = {"rows": rows}
            return {"rows": rows}
            
        else:
            logger.warning(f"Routes API request failed with status {response.status_code}: {response.text}")
            
    except Exception as e:
        logger.warning(f"Error fetching from Google Maps API: {str(e)}. Proceeding to local fallback.")
        
    fallback_matrix = _get_fallback_travel_matrix(origins, destinations, access_token, project)
    tool_context.state["travel_matrix"] = fallback_matrix
    return fallback_matrix

def optimize_route(tool_context: ToolContext) -> dict:
    """Finds the optimal sequence of visits that fits within the 6-hour limit.

    Reads start_address, end_address, start_time, service_requests, and travel_matrix
    directly from session state.

    Returns:
        dict: A schedule breakdown containing ordered visits, tentative times, 
              total travel and service durations, and list of skipped requests.
    """
    # Read from session state
    start_address = tool_context.state.get("start_location")
    end_address = tool_context.state.get("end_location")
    start_time = tool_context.state.get("start_time")
    service_requests = tool_context.state.get("service_requests", [])
    travel_matrix = tool_context.state.get("travel_matrix")
    
    if not all([start_address, end_address, start_time, travel_matrix]):
        raise ValueError("Required session state (start_location, end_location, start_time, travel_matrix) is missing.")

    logger.info(f"Optimizing route starting at {start_address} and ending at {end_address} at {start_time}.")
    num_requests = len(service_requests)
    
    def get_duration_min(from_idx: int, to_idx: int) -> float:
        try:
            elements = travel_matrix["rows"][from_idx]["elements"]
            duration_sec = elements[to_idx]["duration"]["value"]
            return duration_sec / 60.0
        except Exception:
            return 15.0
            
    best_path = []
    best_visited_indices = []
    max_visits = -1
    min_total_duration = float('inf')
    
    MAX_LIMIT_MIN = 360.0
    SERVICE_TIME_MIN = 60.0
    
    def search(curr_idx: int, elapsed_min: float, visited: list, current_path: list):
        nonlocal best_path, best_visited_indices, max_visits, min_total_duration
        
        end_idx = num_requests + 1
        time_to_end = get_duration_min(curr_idx, end_idx)
        
        if elapsed_min + time_to_end <= MAX_LIMIT_MIN:
            num_visits = len(visited)
            total_duration = elapsed_min + time_to_end
            
            if (num_visits > max_visits) or (num_visits == max_visits and total_duration < min_total_duration):
                max_visits = num_visits
                best_path = list(current_path) + [end_idx]
                best_visited_indices = list(visited)
                min_total_duration = total_duration
                
        for next_req_idx in range(1, num_requests + 1):
            if next_req_idx not in visited:
                time_to_next = get_duration_min(curr_idx, next_req_idx)
                potential_time = elapsed_min + time_to_next + SERVICE_TIME_MIN
                time_from_next_to_end = get_duration_min(next_req_idx, end_idx)
                
                if potential_time + time_from_next_to_end <= MAX_LIMIT_MIN:
                    visited.append(next_req_idx)
                    current_path.append(next_req_idx)
                    
                    search(next_req_idx, potential_time, visited, current_path)
                    
                    current_path.pop()
                    visited.pop()

    search(0, 0.0, [], [0])
    
    # Parse start time (e.g. "09:00" or "9:00 AM")
    try:
        clean_time = start_time.upper().replace(" ", "")
        parts = clean_time.split(":")
        start_hour = int("".join(c for c in parts[0] if c.isdigit()))
        start_minute = int("".join(c for c in parts[1] if c.isdigit()))
        if "PM" in clean_time and start_hour < 12:
            start_hour += 12
        elif "AM" in clean_time and start_hour == 12:
            start_hour = 0
    except Exception:
        start_hour = 9
        start_minute = 0
        
    def add_minutes_to_time(hour: int, minute: int, mins_to_add: float) -> str:
        total_mins = hour * 60 + minute + int(round(mins_to_add))
        new_hour = (total_mins // 60) % 24
        new_min = total_mins % 60
        ampm = "AM" if new_hour < 12 else "PM"
        display_hour = new_hour % 12
        if display_hour == 0:
            display_hour = 12
        return f"{display_hour:02d}:{new_min:02d} {ampm}"
        
    ordered_visits = []
    timeline = []
    current_time_offset = 0.0
    
    for i in range(1, len(best_path) - 1):
        prev_node_idx = best_path[i - 1]
        curr_node_idx = best_path[i]
        
        transit_time = get_duration_min(prev_node_idx, curr_node_idx)
        
        # Add Travel segment to timeline
        travel_start = add_minutes_to_time(start_hour, start_minute, current_time_offset)
        current_time_offset += transit_time
        travel_end = add_minutes_to_time(start_hour, start_minute, current_time_offset)
        
        prev_name = "Start Location" if prev_node_idx == 0 else service_requests[prev_node_idx - 1]["customer_name"]
        curr_req = service_requests[curr_node_idx - 1]
        curr_name = curr_req["customer_name"]
        
        timeline.append({
            "type": "Travel",
            "activity": f"Drive from {prev_name} to {curr_name} ({curr_req['customer_address']})",
            "start_time": travel_start,
            "end_time": travel_end,
            "duration_min": round(transit_time, 1)
        })
        
        # Add Service segment to timeline
        service_start = travel_end
        current_time_offset += SERVICE_TIME_MIN
        service_end = add_minutes_to_time(start_hour, start_minute, current_time_offset)
        
        timeline.append({
            "type": "Service",
            "activity": f"Service {curr_name} ({curr_req['request_number']}) at {curr_req['customer_address']}",
            "start_time": service_start,
            "end_time": service_end,
            "duration_min": SERVICE_TIME_MIN
        })
        
        ordered_visits.append({
            "visit_order": i,
            "request_number": curr_req["request_number"],
            "customer_name": curr_name,
            "customer_address": curr_req["customer_address"],
            "service_start": service_start,
            "service_end": service_end,
            "driving_time_to_stop_min": round(transit_time, 1)
        })
        
    if len(best_path) > 1:
        last_service_idx = best_path[-2]
        end_node_idx = best_path[-1]
        last_transit = get_duration_min(last_service_idx, end_node_idx)
        
        # Add final return Travel segment to timeline
        travel_start = add_minutes_to_time(start_hour, start_minute, current_time_offset)
        current_time_offset += last_transit
        travel_end = add_minutes_to_time(start_hour, start_minute, current_time_offset)
        
        last_name = service_requests[last_service_idx - 1]["customer_name"]
        timeline.append({
            "type": "Travel",
            "activity": f"Drive from {last_name} back to End Location ({end_address})",
            "start_time": travel_start,
            "end_time": travel_end,
            "duration_min": round(last_transit, 1)
        })
        
    end_time_str = add_minutes_to_time(start_hour, start_minute, current_time_offset)
    
    visited_req_numbers = {v["request_number"] for v in ordered_visits}
    skipped_requests = [
        r for r in service_requests if r["request_number"] not in visited_req_numbers
    ]
    
    total_travel_time = current_time_offset - (len(ordered_visits) * SERVICE_TIME_MIN)
    
    result = {
        "ordered_visits": ordered_visits,
        "timeline": timeline,
        "skipped_requests": skipped_requests,
        "total_visited": len(ordered_visits),
        "total_skipped": len(skipped_requests),
        "total_travel_time_min": round(total_travel_time, 1),
        "total_service_time_min": len(ordered_visits) * 60,
        "total_duration_min": round(current_time_offset, 1),
        "start_time": add_minutes_to_time(start_hour, start_minute, 0),
        "end_time": end_time_str
    }
    
    # Save to state
    tool_context.state["optimized_route"] = result
    return result

import json
import urllib.parse
import os

def render_intake_ui(tool_context: ToolContext) -> str:
    """Generates the A2UI v0.8 intake form payload.

    Returns:
        str: A2UI JSON string prefixed with ---a2ui_JSON---.
    """
    payload = {
        "a2ui_messages": [
            {
                "beginRendering": {
                    "surfaceId": "route_plan",
                    "root": "root_card"
                }
            },
            {
                "dataModelUpdate": {
                    "surfaceId": "route_plan",
                    "path": "/trip",
                    "contents": [
                        { "key": "start_location", "valueString": "" },
                        { "key": "same_as_start", "valueBoolean": False },
                        { "key": "end_location", "valueString": "" },
                        { "key": "start_time", "valueString": "" }
                    ]
                }
            },
            {
                "surfaceUpdate": {
                    "surfaceId": "route_plan",
                    "components": [
                        {
                            "id": "root_card",
                            "component": {
                                "Card": {
                                    "child": "root_col"
                                }
                            }
                        },
                        {
                            "id": "root_col",
                            "component": {
                                "Column": {
                                    "children": {
                                        "explicitList": [
                                            "title_text",
                                            "start_addr_input",
                                            "same_as_start_checkbox",
                                            "end_addr_input",
                                            "start_time_label",
                                            "start_time_input",
                                            "submit_btn"
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            "id": "title_text",
                            "component": {
                                "Text": {
                                    "text": { "literalString": "Route Planner Intake Form" },
                                    "usageHint": "h2"
                                }
                            }
                        },
                        {
                            "id": "start_addr_input",
                            "component": {
                                "TextField": {
                                    "label": { "literalString": "Starting Address" },
                                    "text": { "path": "/trip/start_location" },
                                    "textFieldType": "shortText"
                                }
                            }
                        },
                        {
                            "id": "same_as_start_checkbox",
                            "component": {
                                "CheckBox": {
                                    "label": { "literalString": "Same as starting address" },
                                    "value": { "path": "/trip/same_as_start" }
                                }
                            }
                        },
                        {
                            "id": "end_addr_input",
                            "component": {
                                "TextField": {
                                    "label": { "literalString": "Ending Address" },
                                    "text": { "path": "/trip/end_location" },
                                    "textFieldType": "shortText"
                                }
                            }
                        },
                        {
                            "id": "start_time_label",
                            "component": {
                                "Text": {
                                    "text": { "literalString": "Start Time (7 AM - 11 AM)" }
                                }
                            }
                        },
                        {
                            "id": "start_time_input",
                            "component": {
                                "DateTimeInput": {
                                    "value": { "path": "/trip/start_time" },
                                    "enableDate": False,
                                    "enableTime": True
                                }
                            }
                        },
                        {
                            "id": "submit_btn",
                            "component": {
                                "Button": {
                                    "child": "submit_btn_txt",
                                    "primary": True,
                                    "action": {
                                        "name": "submit_trip_details",
                                        "context": [
                                            { "key": "start_location", "value": { "path": "/trip/start_location" } },
                                            { "key": "end_location", "value": { "path": "/trip/end_location" } },
                                            { "key": "start_time", "value": { "path": "/trip/start_time" } },
                                            { "key": "same_as_start", "value": { "path": "/trip/same_as_start" } },
                                            { "key": "message", "value": { "literalString": "Plan my route" } }
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            "id": "submit_btn_txt",
                            "component": {
                                "Text": {
                                    "text": { "literalString": "Start Planning" }
                                }
                            }
                        }
                    ]
                }
            }
        ]
    }
    return f"---a2ui_JSON---\n{json.dumps(payload, indent=2)}"

def render_schedule_ui(tool_context: ToolContext) -> str:
    """Generates the A2UI v0.8 schedule dashboard and Google Maps iframe payload.

    Returns:
        str: A2UI JSON string prefixed with ---a2ui_JSON---.
    """
    opt_route = tool_context.state.get("optimized_route")
    start_location = tool_context.state.get("start_location")
    end_location = tool_context.state.get("end_location")
    
    if not opt_route:
        return "---a2ui_JSON---\n{}"
        
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    
    visits = opt_route.get("ordered_visits", [])
    waypoints_list = [v["customer_address"] for v in visits]
    
    # Use raw address strings directly for the Google Maps Embed API to let client-side geocode
    # and resolve actual names/addresses in the map interface instead of raw coordinate numbers.
    origin_str = start_location
    dest_str = end_location
    waypoints_coords = waypoints_list
    
    base_url = "https://www.google.com/maps/embed/v1/directions"
    
    # Construct the query string using standard URL encoding. Include standard 'origin' directly.
    # Since the Google Maps Embed API prioritizes the first occurrence of the 'origin' parameter
    # in the query string, the platform's appended parameter will be ignored by Google Maps.
    params = {
        "key": api_key,
        "origin": origin_str,
        "destination": dest_str,
        "mode": "driving"
    }
    if waypoints_coords:
        params["waypoints"] = "|".join(waypoints_coords)
        
    query_string = urllib.parse.urlencode(params)
    embed_url = f"{base_url}?{query_string}"
    
    components = [
        {
            "id": "root_card",
            "component": {
                "Card": {
                    "child": "root_col"
                }
            }
        },
        {
            "id": "root_col",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": [
                            "title_text",
                            "summary_card",
                            "timeline_card",
                            "map_card"
                        ]
                    }
                }
            }
        },
        {
            "id": "timeline_card",
            "component": {
                "Card": {
                    "child": "timeline_row_container"
                }
            }
        },
        {
            "id": "title_text",
            "component": {
                "Text": {
                    "text": { "literalString": "Optimized Route Schedule" },
                    "usageHint": "h2"
                }
            }
        },
        {
            "id": "summary_card",
            "component": {
                "Card": {
                    "child": "summary_col"
                }
            }
        },
        {
            "id": "summary_col",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": [
                            "summary_title",
                            "summary_visited",
                            "summary_skipped",
                            "summary_times"
                        ]
                    }
                }
            }
        },
        {
            "id": "summary_title",
            "component": {
                "Text": {
                    "text": { "literalString": "Workday Summary" },
                    "usageHint": "h3"
                }
            }
        },
        {
            "id": "summary_visited",
            "component": {
                "Text": {
                    "text": { "literalString": f"Total Serviced: {opt_route['total_visited']} customers (Duration: {round(opt_route['total_duration_min']/60.0, 1)}h / 6h limit)" }
                }
            }
        },
        {
            "id": "summary_skipped",
            "component": {
                "Text": {
                    "text": { "literalString": f"Skipped: {', '.join([r['request_number'] for r in opt_route['skipped_requests']]) if opt_route['skipped_requests'] else 'None'}" }
                }
            }
        },
        {
            "id": "summary_times",
            "component": {
                "Text": {
                    "text": { "literalString": f"Start Time: {opt_route['start_time']} | End Time: {opt_route['end_time']}" }
                }
            }
        }
    ]
    
    timeline = opt_route.get("timeline", [])
    
    col_type_children = ["header_type"]
    col_activity_children = ["header_activity"]
    col_time_children = ["header_time"]
    col_duration_children = ["header_duration"]
    
    table_components = [
        {
            "id": "timeline_row_container",
            "component": {
                "Row": {
                    "children": {
                        "explicitList": [
                            "col_type",
                            "col_activity",
                            "col_time",
                            "col_duration"
                        ]
                    },
                    "distribution": "spaceBetween"
                }
            }
        },
        {
            "id": "header_type",
            "component": {
                "Text": {
                    "text": { "literalString": "Type" },
                    "usageHint": "h3"
                }
            }
        },
        {
            "id": "header_activity",
            "component": {
                "Text": {
                    "text": { "literalString": "Activity" },
                    "usageHint": "h3"
                }
            }
        },
        {
            "id": "header_time",
            "component": {
                "Text": {
                    "text": { "literalString": "Time Range" },
                    "usageHint": "h3"
                }
            }
        },
        {
            "id": "header_duration",
            "component": {
                "Text": {
                    "text": { "literalString": "Duration" },
                    "usageHint": "h3"
                }
            }
        }
    ]
    
    for idx, item in enumerate(timeline):
        item_type_id = f"item_type_{idx}"
        item_act_id = f"item_act_{idx}"
        item_time_id = f"item_time_{idx}"
        item_dur_id = f"item_dur_{idx}"
        
        col_type_children.append(item_type_id)
        col_activity_children.append(item_act_id)
        col_time_children.append(item_time_id)
        col_duration_children.append(item_dur_id)
        
        raw_act = item["activity"]
        clean_act = raw_act
        if "Drive from" in raw_act:
            try:
                parts = raw_act.split("Drive from ")[1].split(" to ")
                from_name = parts[0]
                to_name = parts[1].split(" (")[0]
                clean_act = f"Drive: {from_name} -> {to_name}"
            except Exception:
                pass
        elif "Service " in raw_act:
            try:
                parts = raw_act.split("Service ")[1].split(" at ")
                svc_name = parts[0]
                clean_act = f"Service: {svc_name}"
            except Exception:
                pass
                
        type_emoji = "🚗 Drive" if item["type"] == "Travel" else "📍 Service"
        
        table_components.extend([
            {
                "id": item_type_id,
                "component": {
                    "Text": {
                        "text": { "literalString": type_emoji },
                        "usageHint": "body"
                    }
                }
            },
            {
                "id": item_act_id,
                "component": {
                    "Text": {
                        "text": { "literalString": clean_act },
                        "usageHint": "body"
                    }
                }
            },
            {
                "id": item_time_id,
                "component": {
                    "Text": {
                        "text": { "literalString": f"{item['start_time']} - {item['end_time']}" },
                        "usageHint": "body"
                    }
                }
            },
            {
                "id": item_dur_id,
                "component": {
                    "Text": {
                        "text": { "literalString": f"{item['duration_min']} min" },
                        "usageHint": "body"
                    }
                }
            }
        ])
        
    table_components.extend([
        {
            "id": "col_type",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": col_type_children
                    }
                }
            }
        },
        {
            "id": "col_activity",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": col_activity_children
                    }
                }
            }
        },
        {
            "id": "col_time",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": col_time_children
                    }
                }
            }
        },
        {
            "id": "col_duration",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": col_duration_children
                    }
                }
            }
        }
    ])
    
    components.extend(table_components)
    
    components.extend([
        {
            "id": "map_card",
            "component": {
                "Card": {
                    "child": "map_iframe"
                }
            }
        },
        {
            "id": "map_iframe",
            "component": {
                "WebFrameUrl": {
                    "url": {
                        "literalString": embed_url
                    },
                    "height": 450
                }
            }
        }
    ])
    
    payload = {
        "a2ui_messages": [
            {
                "beginRendering": {
                    "surfaceId": "route_plan",
                    "root": "root_card"
                }
            },
            {
                "surfaceUpdate": {
                    "surfaceId": "route_plan",
                    "components": components
                }
            }
        ]
    }
    
    return f"---a2ui_JSON---\n{json.dumps(payload, indent=2)}"

