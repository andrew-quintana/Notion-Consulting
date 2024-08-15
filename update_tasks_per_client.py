import requests
from datetime import datetime

def handler(pd: "pipedream"):
    # Your Notion API token
    notion_token = pd.inputs["notion"]["$auth"]["oauth_access_token"]

    # Define your database and template IDs
    clients_database_id = "01d60b02ab8f4dc48cb2081bc08872c5"
    tasks_database_id = "c19166634c39401783b9013f0904865e"
    update_template = "67283d7b53784976a566d59cb3f40c98" 
    review_template = "84cffcd367d242a79e4018086fb173a8"
    dev_template = "20367a60ded248f6b00dc7b12e073692"

    # Set up headers for the API requests
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    # Step 1: Query the Clients database to find pages with "Phase" = "Sustaining: Update Program"
    query_url = f"https://api.notion.com/v1/databases/{clients_database_id}/query"
    query_payload = {
        "filter": {
            "property": "Phase",
            "select": {
                "equals": "Sustaining: Update Program"
            }
        }
    }

    response = requests.post(query_url, json=query_payload, headers=headers)
    print("Query Response:", response.json())

    clients = response.json().get("results", [])

    if not clients:
        print("No clients found with 'Sustaining: Update Program'.")
    else:
        for client in clients:
            client_id = client["id"]
            client_name = client["properties"]["Name"]["title"][0]["text"]["content"]
            task_date = datetime.today().strftime('%Y-%m-%d')

            # Get the current Update Counter and Update Freq (weeks)
            update_counter = client["properties"].get("Update Counter", {}).get("number", 0)
            update_freq_weeks = client["properties"].get("Update Freq (weeks)", {}).get("number", 0)

            # Fetch the template page's update_icon, update_cover, and content
            template_page_response = requests.get(
                f"https://api.notion.com/v1/pages/{update_template}",
                headers=headers
            )
            template_page = template_page_response.json()
            update_icon = template_page.get("icon")
            update_cover = template_page.get("cover")

            template_content_response = requests.get(
                f"https://api.notion.com/v1/blocks/{update_template}/children",
                headers=headers
            )
            template_content = template_content_response.json().get("results", [])

            # Step 2: Increment the "Update Counter" property for the client
            new_update_counter = update_counter + 1

            # Update the client with the new counter value
            update_client_url = f"https://api.notion.com/v1/pages/{client_id}"
            update_client_payload = {
                "properties": {
                    "Update Counter": {
                        "number": new_update_counter
                    }
                }
            }
            update_client_response = requests.patch(update_client_url, json=update_client_payload, headers=headers)
            
            if update_client_response.status_code != 200:
                print(f"Error updating counter for {client_name}: {update_client_response.status_code}")
                print(f"Error response: {update_client_response.json()}")

            create_task_url = "https://api.notion.com/v1/pages"

            if new_update_counter == update_freq_weeks:
                # Fetch the dev template content
                    dev_template_content_response = requests.get(
                        f"https://api.notion.com/v1/blocks/{review_template}/children",
                        headers=headers
                    )
                    dev_template_content = dev_template_content_response.json().get("results", [])

                    # Create a new task in the Tasks database using the dev template content
                    dev_task_name = f"{client_name} Program Update"

                    # Fetch the template page's review_icon, review_cover, and content
                    template_page_response = requests.get(
                        f"https://api.notion.com/v1/pages/{review_template}",
                        headers=headers
                    )
                    template_page = template_page_response.json()
                    review_icon = template_page.get("icon")
                    review_cover = template_page.get("cover")

                    template_content_response = requests.get(
                        f"https://api.notion.com/v1/blocks/{review_template}/children",
                        headers=headers
                    )
                    template_content = template_content_response.json().get("results", [])

                    create_dev_task_payload = {
                        "parent": {
                            "database_id": tasks_database_id
                        },
                        "properties": {
                            "Name": {
                                "title": [
                                    {
                                        "text": {
                                            "content": dev_task_name
                                        }
                                    }
                                ]
                            },
                            "Client": {
                                "relation": [
                                    {
                                        "id": client_id
                                    }
                                ]
                            },
                            "Date": {
                                "date": {
                                    "start": task_date
                                }
                            }
                        },
                        "children": dev_template_content,  # Use the content fetched from the primary template
                        "icon": review_icon,                   # Include the update_icon (emoji) from the template
                        "cover": review_cover                  # Include the update_cover image from the template
                    }

                    dev_task_response = requests.post(create_task_url, json=create_dev_task_payload, headers=headers)
                    
                    if dev_task_response.status_code != 200:
                        print(f"Error creating dev task for {client_name}: {dev_task_response.status_code}")
                        print(f"Error response: {dev_task_response.json()}")
                    else:
                        dev_task_id = dev_task_response.json().get("id")
                        print(f"Created dev task for {client_name}: {dev_task_id}")

                    # Update counter to 0 once new Program Development task created
                    new_update_counter = 0

                    update_client_url = f"https://api.notion.com/v1/pages/{client_id}"
                    update_client_payload = {
                        "properties": {
                            "Update Counter": {
                                "number": new_update_counter
                            }
                        }
                    }
                    update_client_response = requests.patch(update_client_url, json=update_client_payload, headers=headers)
                    
                    if update_client_response.status_code != 200:
                        print(f"Error updating counter for {client_name}: {update_client_response.status_code}")
                        print(f"Error response: {update_client_response.json()}")

            else:
                task_name = f"{client_name} Workout Update"
                
                # Step 3: Create a new task in the Tasks database using the primary template content
                create_task_payload = {
                    "parent": {
                        "database_id": tasks_database_id
                    },
                    "properties": {
                        "Name": {
                            "title": [
                                {
                                    "text": {
                                        "content": task_name
                                    }
                                }
                            ]
                        },
                        "Client": {
                            "relation": [
                                {
                                    "id": client_id
                                }
                            ]
                        },
                        "Date": {
                            "date": {
                                "start": task_date
                            }
                        }
                    },
                    "children": template_content,  # Use the content fetched from the primary template
                    "icon": update_icon,                   # Include the update_icon (emoji) from the template
                    "cover": update_cover                  # Include the update_cover image from the template
                }

                task_response = requests.post(create_task_url, json=create_task_payload, headers=headers)
                
                if task_response.status_code != 200:
                    print(f"Error creating task for {client_name}: {task_response.status_code}")
                    print(f"Error response: {task_response.json()}")
                else:
                    task_id = task_response.json().get("id")
                    print(f"Created task for {client_name}: {task_id}")

                # Step 4: Check if the update_counter equals "Update Freq (weeks)" minus 1
                if new_update_counter == update_freq_weeks - 1:
                    print(f"Creating additional task for {client_name} using the secondary template")

                    # Fetch the secondary template content
                    secondary_template_content_response = requests.get(
                        f"https://api.notion.com/v1/blocks/{review_template}/children",
                        headers=headers
                    )
                    secondary_template_content = secondary_template_content_response.json().get("results", [])

                    # Create a new task in the Tasks database using the secondary template content
                    secondary_task_name = f"{client_name} Program Update"

                    # Fetch the template page's review_icon, review_cover, and content
                    template_page_response = requests.get(
                        f"https://api.notion.com/v1/pages/{review_template}",
                        headers=headers
                    )
                    template_page = template_page_response.json()
                    review_icon = template_page.get("icon")
                    review_cover = template_page.get("cover")

                    template_content_response = requests.get(
                        f"https://api.notion.com/v1/blocks/{review_template}/children",
                        headers=headers
                    )
                    template_content = template_content_response.json().get("results", [])

                    create_secondary_task_payload = {
                        "parent": {
                            "database_id": tasks_database_id
                        },
                        "properties": {
                            "Name": {
                                "title": [
                                    {
                                        "text": {
                                            "content": secondary_task_name
                                        }
                                    }
                                ]
                            },
                            "Client": {
                                "relation": [
                                    {
                                        "id": client_id
                                    }
                                ]
                            },
                            "Date": {
                                "date": {
                                    "start": task_date
                                }
                            }
                        },
                        "children": secondary_template_content,  # Use the content fetched from the primary template
                        "icon": review_icon,                   # Include the update_icon (emoji) from the template
                        "cover": review_cover                  # Include the update_cover image from the template
                    }

                    secondary_task_response = requests.post(create_task_url, json=create_secondary_task_payload, headers=headers)
                    
                    if secondary_task_response.status_code != 200:
                        print(f"Error creating secondary task for {client_name}: {secondary_task_response.status_code}")
                        print(f"Error response: {secondary_task_response.json()}")
                    else:
                        secondary_task_id = secondary_task_response.json().get("id")
                        print(f"Created secondary task for {client_name}: {secondary_task_id}")