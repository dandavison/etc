     savannah_data = ecosystems.savannah_data
     giraffe_dob = parser.parse(savannah_data["giraffe"]["date_of_birth"]).date()
     giraffe_first_name = savannah_data["giraffe"]["first_name"]
     giraffe_last_name = savannah_data["giraffe"]["last_name"]
     eagle_id = get_eagle_id()
