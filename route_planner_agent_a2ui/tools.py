from google.adk.tools.tool_context import ToolContext
from google.auth import default
from google.auth.transport.requests import Request
import logging
import requests
import json

def fetch_service_requests(tool_context: ToolContext) -> dict:
    """
    Fetches the list of service requests for the day.
    
    Returns:
        dict: A dictionary containing a list of requests, each with an address.
    """
    # Mocking 10 requests in a geographic area (Main St)
    requests = [
        {"id": 1, "customer": "Alice", "address": "100 Peachtree St NW, Atlanta, GA 30303"},
        {"id": 2, "customer": "Bob", "address": "1015 W Peachtree St NW, Atlanta, GA 30309"},
        {"id": 3, "customer": "Charlie", "address": "2450 Piedmont Rd NE, Atlanta, GA 30324"},
        {"id": 4, "customer": "David", "address": "3393 Peachtree Rd NE, Atlanta, GA 30326"},
        {"id": 5, "customer": "Eve", "address": "1200 Ponce De Leon Ave NE, Atlanta, GA 30306"},
        {"id": 6, "customer": "Frank", "address": "515 Decatur St SE, Atlanta, GA 30312"},
        {"id": 7, "customer": "Grace", "address": "200 Galleria Pkwy, Atlanta, GA 30339"},
        {"id": 8, "customer": "Hank", "address": "1000 Robert E Lee Blvd, Stone Mountain, GA 30083"},
        {"id": 9, "customer": "Ivy", "address": "1234 Powers Ferry Rd, Marietta, GA 30067"},
        {"id": 10, "customer": "Jack", "address": "5000 Northland Dr, Atlanta, GA 30342"},
    ]
    return {"status": "success", "requests": requests}

def get_street_number(address: str) -> int:
    try:
        return int(address.split()[0])
    except (IndexError, ValueError):
        return 0

def calculate_routes(start_address: str, end_address: str, customer_addresses: list[str], tool_context: ToolContext) -> dict:
    """
    Calculates travel times between all locations using Google Routes API or fallback mock.
    
    Args:
        start_address: The starting address.
        end_address: The ending address.
        customer_addresses: List of customer addresses.
        
    Returns:
        dict: A matrix of travel times (in minutes) between all locations.
    """
    all_locations = [start_address] + customer_addresses + [end_address]
    n = len(all_locations)
    
    # Try real API first
    try:
        # 1. Get API Key from environment
        import os
        api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
        
        # 2. Build Payload
        origins = [{"waypoint": {"address": addr}} for addr in all_locations]
        destinations = [{"waypoint": {"address": addr}} for addr in all_locations]
        
        payload = {
            "origins": origins,
            "destinations": destinations,
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE"
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "originIndex,destinationIndex,duration,distanceMeters,status"
        }
        
        url = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        matrix = [[0] * n for _ in range(n)]
        
        for element in data:
            origin_idx = element.get("originIndex", 0)
            dest_idx = element.get("destinationIndex", 0)
            duration_str = element.get("duration", "0s")
            duration_sec = int(duration_str.rstrip('s'))
            duration_min = duration_sec // 60
            matrix[origin_idx][dest_idx] = duration_min
            
        return {
            "status": "success",
            "locations": all_locations,
            "travel_time_matrix": matrix,
            "mode": "real"
        }
        
    except Exception as e:
        logging.error(f"Failed to call Routes API: {e}. Falling back to mock.")
        
        # Fallback Mock Logic
        matrix = [[0] * n for _ in range(n)]
        

                
        for i in range(n):
            for j in range(n):
                num_i = get_street_number(all_locations[i])
                num_j = get_street_number(all_locations[j])
                matrix[i][j] = abs(num_i - num_j) // 100 * 5
                
        return {
            "status": "success", 
            "locations": all_locations,
            "travel_time_matrix": matrix,
            "mode": "mock"
        }

def optimize_route(travel_time_matrix: list[list[int]], locations: list[str], requests: list[dict] = None, tool_context: ToolContext = None) -> dict:
    """
    Optimizes the route to fit within 6 hours (360 minutes).
    
    Args:
        travel_time_matrix: Matrix of travel times between locations.
        locations: List of location names corresponding to the matrix.
        requests: List of service requests containing customer names.
        
    Returns:
        dict: Optimized sequence of visits and schedule.
    """
    n = len(locations)
    visited = [False] * n
    visited[0] = True # Start is visited
    
    current_node = 0
    route = []
    total_time = 0
    service_time = 60 # 1 hour
    time_limit = 360 # 6 hours
    
    while True:
        best_next = -1
        best_travel = float('inf')
        
        for next_node in range(1, n - 1):
            if not visited[next_node]:
                travel = travel_time_matrix[current_node][next_node]
                if travel < best_travel:
                    best_travel = travel
                    best_next = next_node
                    
        if best_next == -1:
            break # No more unvisited customers
            
        travel_to_next = travel_time_matrix[current_node][best_next]
        travel_to_end = travel_time_matrix[best_next][n - 1]
        
        potential_time = total_time + travel_to_next + service_time
        
        if potential_time + travel_to_end <= time_limit:
            route.append(best_next)
            visited[best_next] = True
            total_time = potential_time
            current_node = best_next
        else:
            break
            
    total_time += travel_time_matrix[current_node][n - 1]
    
    schedule = []
    current_time_offset = 0
    current_node = 0
    
    for i, node in enumerate(route):
        travel = travel_time_matrix[current_node][node]
        
        # Find customer name
        customer_name = "N/A"
        address = locations[node]
        if requests:
            for req in requests:
                if req["address"] == address:
                    customer_name = req["customer"]
                    break
                
        # 1. Add Travel Step (if travel time > 0)
        if travel > 0:
            schedule.append({
                "activity": f"Travel to {locations[node]}",
                "customer": "N/A",
                "start_offset": current_time_offset,
                "end_offset": current_time_offset + travel,
                "duration": travel
            })
            current_time_offset += travel
            
        # 2. Add Visit Step
        schedule.append({
            "activity": f"Visit {locations[node]}",
            "customer": customer_name,
            "start_offset": current_time_offset,
            "end_offset": current_time_offset + service_time,
            "duration": service_time
        })
        current_time_offset += service_time
        current_node = node
        
    # Add Final Travel to End location
    travel_to_end = travel_time_matrix[current_node][n - 1]
    if travel_to_end > 0:
        schedule.append({
            "activity": f"Travel to {locations[-1]}",
            "customer": "N/A",
            "start_offset": current_time_offset,
            "end_offset": current_time_offset + travel_to_end,
            "duration": travel_to_end
        })
        current_time_offset += travel_to_end
        
    return {
        "status": "success",
        "optimized_route": [locations[i] for i in route],
        "schedule": schedule,
        "total_customers_handled": len(route),
        "total_time_used": total_time
    }

def geocode_address_api(address: str, api_key: str) -> dict:
    """Geocodes an address using Google Geocoding API."""
    import requests
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": api_key
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data["status"] == "OK":
            location = data["results"][0]["geometry"]["location"]
            return {"lat": location["lat"], "lng": location["lng"]}
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Geocoding failed for {address}: {e}")
    return None

def send_route_plan_ui(schedule: list, skipped_customers: list, start_address: str, end_address: str = None, start_coords: dict = None, end_coords: dict = None, start_time: str = "09:00 AM", tool_context: ToolContext = None) -> dict:
    """
    Generates the A2UI JSON for the route plan and returns it.
    
    Args:
        schedule: List of schedule items.
        skipped_customers: List of skipped customer names.
        
    Returns:
        dict: A dictionary containing the generated A2UI JSON string.
    """
    import json
    
    coords = {
        "100 Peachtree St NW, Atlanta, GA 30303": {"lat": 33.7572, "lng": -84.3888},
        "1015 W Peachtree St NW, Atlanta, GA 30309": {"lat": 33.7826, "lng": -84.3885},
        "2450 Piedmont Rd NE, Atlanta, GA 30324": {"lat": 33.8228, "lng": -84.3695},
        "3393 Peachtree Rd NE, Atlanta, GA 30326": {"lat": 33.8463, "lng": -84.3621},
        "1200 Ponce De Leon Ave NE, Atlanta, GA 30306": {"lat": 33.7734, "lng": -84.3499},
        "515 Decatur St SE, Atlanta, GA 30312": {"lat": 33.7500, "lng": -84.3750},
        "200 Galleria Pkwy, Atlanta, GA 30339": {"lat": 33.8830, "lng": -84.4670},
        "1000 Robert E Lee Blvd, Stone Mountain, GA 30083": {"lat": 33.8050, "lng": -84.1450},
        "1234 Powers Ferry Rd, Marietta, GA 30067": {"lat": 33.9100, "lng": -84.4400},
        "5000 Northland Dr, Atlanta, GA 30342": {"lat": 33.8900, "lng": -84.3800},
    }
    
    if start_coords:
        coords[start_address] = start_coords
        
    components = []
    
    # Root column
    components.append({
        "id": "root_col",
        "component": {
            "Column": {
                "children": { "explicitList": ["map_component", "timeline_col", "footer_card"] }
            }
        }
    })
    
    # Build markers and polyline
    markers = []
    path_coords = []
    
    start_addr = start_address.strip() if start_address else ""
    # Find matching key in coords ignoring case and whitespace
    # Resolve Start Coordinates
    matching_key = None
    for key in coords:
        if key.lower().strip() == start_addr.lower():
            matching_key = key
            break
            
    if matching_key:
        start_coords = coords[matching_key]
    elif not start_coords:
        # Try real-time geocoding first!
        import os
        api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
        if api_key:
            start_coords = geocode_address_api(start_addr, api_key)
            
        if not start_coords:
            num = get_street_number(start_addr)
            start_coords = {"lat": 33.75 + num/100000, "lng": -84.38 + num/100000}
            
            
    # Resolve End Coordinates
    matching_end_key = None
    if end_address:
        for key in coords:
            if key.lower().strip() == end_address.lower():
                matching_end_key = key
                break
                
    if matching_end_key:
        end_coords = coords[matching_end_key]
    elif end_address and not end_coords:
        # Try real-time geocoding first!
        import os
        api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
        if api_key:
            end_coords = geocode_address_api(end_address, api_key)
            
        if not end_coords:
            num = get_street_number(end_address)
            end_coords = {"lat": 33.75 + num/100000, "lng": -84.38 + num/100000}
            


    # Add Markers
    if start_coords:
        markers.append({
            "lat": start_coords["lat"],
            "lng": start_coords["lng"],
            "label": f"Start: {start_addr.split(',')[0]}"
        })
        path_coords.append({"lat": start_coords["lat"], "lng": start_coords["lng"]})
        
    visit_count = 0
    for item in schedule:
        if "Visit" in item['activity']:
            addr = item['activity'].replace("Visit ", "")
            if addr in coords:
                visit_count += 1
                markers.append({
                    "lat": coords[addr]["lat"],
                    "lng": coords[addr]["lng"],
                    "label": f"{visit_count}. {item['customer']}"
                })
                path_coords.append({"lat": coords[addr]["lat"], "lng": coords[addr]["lng"]})
                
    # Add End marker if provided
    if end_coords:
        markers.append({
            "lat": end_coords["lat"],
            "lng": end_coords["lng"],
            "label": "End"
        })
        
    # Return to start in polyline
    if start_coords:
        path_coords.append({"lat": start_coords["lat"], "lng": start_coords["lng"]})
                
    # Add InteractiveMap component
    components.append({
        "id": "map_component",
        "component": {
            "InteractiveMap": {
                "id": "route_map",
                "props": {
                    "markers": markers
                }
            }
        }
    })
        
    from datetime import datetime, timedelta
    try:
        if "T" in start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        else:
            start_dt = datetime.strptime(start_time, "%I:%M %p")
    except Exception as e:
        logging.warning(f"Failed to parse start_time: {e}. Using default 9:00 AM.")
        start_dt = datetime.strptime("09:00 AM", "%I:%M %p")

    # Header Row
    components.append({
        "id": "header_time",
        "weight": 1,
        "component": { "Text": { "text": { "literalString": "Time" } } }
    })
    components.append({
        "id": "header_activity",
        "weight": 3,
        "component": { "Text": { "text": { "literalString": "Activity" } } }
    })
    components.append({
        "id": "header_action",
        "weight": 1,
        "component": { "Text": { "text": { "literalString": "Action" } } }
    })
    
    components.append({
        "id": "header_row",
        "component": { "Row": { "children": { "explicitList": ["header_time", "header_activity", "header_action"] } } }
    })
    
    timeline_children = ["header_row"]
    
    for i, item in enumerate(schedule):
        time_id = f"time_{i}"
        activity_id = f"activity_{i}"
        action_id = f"action_{i}"
        row_id = f"row_{i}"
        
        # Calculate time range
        item_start_dt = start_dt + timedelta(minutes=item['start_offset'])
        item_end_dt = start_dt + timedelta(minutes=item['end_offset'])
        time_range = f"{item_start_dt.strftime('%I:%M %p')} - {item_end_dt.strftime('%I:%M %p')}"
        
        components.append({
            "id": time_id,
            "weight": 1,
            "component": { "Text": { "text": { "literalString": time_range } } }
        })
        
        activity_desc = item['activity']
        if "Visit" in activity_desc:
            activity_desc = f"Visit: {item['customer']}\n{activity_desc.replace('Visit ', '')}"
            
        components.append({
            "id": activity_id,
            "weight": 3,
            "component": { "Text": { "text": { "literalString": activity_desc } } }
        })
        
        if "Travel" in item['activity']:
            btn_text_id = f"btn_text_{i}"
            components.append({
                "id": btn_text_id,
                "component": { "Text": { "text": { "literalString": "View Map" } } }
            })
            components.append({
                "id": action_id,
                "weight": 1,
                "component": { "Button": { "child": btn_text_id, "action": { "name": "open_map" } } }
            })
        else:
            components.append({
                "id": action_id,
                "weight": 1,
                "component": { "Text": { "text": { "literalString": "-" } } }
            })
            
        components.append({
            "id": row_id,
            "component": { "Row": { "children": { "explicitList": [time_id, activity_id, action_id] } } }
        })
        
        timeline_children.append(row_id)
        
    components.append({
        "id": "timeline_col",
        "component": {
            "Column": {
                "children": { "explicitList": timeline_children }
            }
        }
    })
    
    # Footer Card
    components.append({
        "id": "footer_text",
        "component": {
            "Text": {
                "text": { "literalString": f"Skipped: {', '.join(skipped_customers)}" }
            }
        }
    })
    components.append({
        "id": "footer_card",
        "component": {
            "Card": { "child": "footer_text" }
        }
    })
    
    a2ui_payload = {
        "a2ui_messages": [
            {
                "version": "v0.8",
                "beginRendering": {
                    "surfaceId": "main",
                    "root": "root_col"
                }
            },
            {
                "version": "v0.8",
                "surfaceUpdate": {
                    "surfaceId": "main",
                    "components": components
                }
            }
        ]
    }
    
    return {"status": "success", "a2ui_json": json.dumps(a2ui_payload)}

def send_intake_form(tool_context: ToolContext) -> dict:
    """Generates the A2UI JSON for the intake form."""
    import json
    import time
    suffix = str(int(time.time()))
    
    components = [
        {
            "id": "root_col",
            "component": { "Column": { "children": { "explicitList": ["start_addr", "end_addr", "same_addr", "start_time", "submit_btn"] } } }
        },
        {
            "id": "start_addr",
            "component": { "TextField": { "label": { "literalString": "Starting Address" }, "text": { "path": "/start_address" }, "textFieldType": "shortText" } }
        },
        {
            "id": "end_addr",
            "component": { "TextField": { "label": { "literalString": "Ending Address" }, "text": { "path": "/end_address" }, "textFieldType": "shortText" } }
        },
        {
            "id": "same_addr",
            "component": { "CheckBox": { "label": { "literalString": "Same address?" }, "value": { "path": "same_address" } } }
        },
        {
            "id": "start_time",
            "component": { "DateTimeInput": { "label": { "literalString": "Start Time" }, "value": { "path": "start_time" }, "enableDate": True, "enableTime": True } }
        },
        {
            "id": "submit_text",
            "component": { "Text": { "text": { "literalString": "Plan Route" } } }
        },
        {
            "id": "submit_btn",
            "component": {
                "Button": {
                    "child": "submit_text",
                    "action": {
                        "name": "submit_route_plan",
                        "context": [
                            {"key": "message", "value": {"literalString": "Plan my route with the provided details."}},
                            {"key": "start_address", "value": {"path": "/start_address"}},
                            {"key": "end_address", "value": {"path": "/end_address"}},
                            {"key": "same_address", "value": {"path": "/same_address"}},
                            {"key": "start_time", "value": {"path": "/start_time"}},
                            {"key": "start_lat", "value": {"path": "/start_lat"}},
                            {"key": "start_lng", "value": {"path": "/start_lng"}},
                            {"key": "end_lat", "value": {"path": "/end_lat"}},
                            {"key": "end_lng", "value": {"path": "/end_lng"}}
                        ]
                    }
                }
            }
        }
    ]
    
    a2ui_payload = {
        "a2ui_messages": [
            {
                "beginRendering": {
                    "surfaceId": "main",
                    "root": "root_col"
                }
            },
            {
                "surfaceUpdate": {
                    "surfaceId": "main",
                    "components": components
                }
            },
            {
                "dataModelUpdate": {
                    "surfaceId": "main",
                    "path": "/",
                    "contents": [
                        {"key": "same_address", "valueBoolean": False},
                        {"key": "start_time", "valueString": "2026-05-19T09:00:00Z"}
                    ]
                }
            }
        ]
    }
    return {"status": "success", "a2ui_json": json.dumps(a2ui_payload)}
