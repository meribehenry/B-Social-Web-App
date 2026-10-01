from datetime import timedelta
from rest_framework.response import Response
from rest_framework import status


class APISuccessResponseHandler():

    
    def success(self, data=None, message="Success", status_code=status.HTTP_200_OK, pagination=None) -> Response:
        """For any success response, examples 200, 201, 204 etc."""
        body = {}

        if message:
            body["message"] = message

        if data:
            body["data"] = data

        if pagination:
            body["pagination"] = pagination

        return  Response(body, status=status_code)
    
    def success_extra_data_cookie(
        self,
        name="cookie", 
        data=None, 
        message="Success", 
        status_code=status.HTTP_200_OK,
        pagination=None, 
        value="cookie", 
        httponly=True, 
        secure=False, 
        expires_at=(30 * 24 * 60 * 60), 
        samesite='lax'
    ):
        
        response = self.success(data=data, message=message, status_code=status_code, pagination=pagination)
        
        response.set_cookie(
            key=name,
            value=value,
            httponly=httponly,
            secure=secure,
            samesite=samesite,
            max_age=expires_at
        )
        return response

    
class APIErrorResponseHandler():  
    
    def error(self, error=None, message="An error occurred", status_code=status.HTTP_400_BAD_REQUEST, data=None):
        body = {}

        if error: body["error"] = error
        if message: body["message"] = message
        if data: body["data"] = data

        return Response(body, status=status_code)



class ServiceResponseBuilder():

    def result(self, message=None, data=None, status_code=status.HTTP_200_OK, pagination=None):
        result = {
            "status_code": status_code
        }

        if data: result["data"] = data
        if message: result["message"] = message
        if pagination: result["pagination"] = pagination

        return result
    

    def internal_server_error(self, message="An error occured"):
        error = {
            "error": "Internal server error", 
            "message": f"Please try again", 
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
        
        return error
    
    def bad_request_error(self, message="The request you sent is invalid"):
        error = {
            "error": "Bad Request", 
            "message":message, 
            "status_code": status.HTTP_400_BAD_REQUEST
            }
        
        return error
    
    def not_found_error(self, message="Resource not found"):
        error = {
            "error": "Not found", 
            "message":message, 
            "status_code": status.HTTP_404_NOT_FOUND
            }
        
        return error
    
    def forbidden_error(self, message="You are unauthorized"):
        error = {
            "error": "Unauthorized", 
            "message":message, 
            "status_code": status.HTTP_403_FORBIDDEN
            }
        
        return error
    
    def conflict_error(self, message="Resource already exists"):
        error = {
            "error": "Conflict error", 
            "message":message, 
            "status_code": status.HTTP_409_CONFLICT
            }
        
        return error
    
    def validation_error(self, message="Invalid. Please try again"):
        error = {
            "error": "Validation error", 
            "message":message, 
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY
            }
        
        return error
    
    def unauthenticated_error(self, message="Please login to access this page"):
        error = {
            "error": "Unauthenticated", 
            "message":message, 
            "status_code": status.HTTP_401_UNAUTHORIZED
            }
        
        return error