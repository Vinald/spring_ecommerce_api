# Request validation schemas using marshmallow.
# Every API endpoint that accepts form data has a corresponding schema here.
# Schemas are used to validate and deserialise incoming request.form fields
# before they reach the handler logic, preventing KeyError 500s and enforcing
# type/length constraints at the boundary.
