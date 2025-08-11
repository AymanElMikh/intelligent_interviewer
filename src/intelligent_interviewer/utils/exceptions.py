# utils/exceptions.py
from typing import Optional, Dict, Any, List
from http import HTTPStatus


class BaseApplicationError(Exception):
    """Base exception class for all application errors"""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
        super().__init__(self.message)
    
    def __str__(self) -> str:
        return f"{self.code}: {self.message}"
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message='{self.message}', "
            f"code='{self.code}', "
            f"details={self.details})"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization"""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
            "type": self.__class__.__name__
        }


class DatabaseError(BaseApplicationError):
    """Raised when database operations fail"""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if operation:
            details['operation'] = operation
        if table:
            details['table'] = table
        
        super().__init__(message, details=details, **kwargs)


class NotFoundError(BaseApplicationError):
    """Raised when a requested resource is not found"""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if resource_type:
            details['resource_type'] = resource_type
        if resource_id:
            details['resource_id'] = resource_id
        
        super().__init__(message, details=details, **kwargs)


class ValidationError(BaseApplicationError):
    """Raised when data validation fails"""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        validation_errors: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)
        if validation_errors:
            details['validation_errors'] = validation_errors
        
        super().__init__(message, details=details, **kwargs)


class AuthenticationError(BaseApplicationError):
    """Raised when authentication fails"""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        auth_type: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if auth_type:
            details['auth_type'] = auth_type
        
        super().__init__(message, details=details, **kwargs)


class AuthorizationError(BaseApplicationError):
    """Raised when authorization fails"""
    
    def __init__(
        self,
        message: str = "Access denied",
        resource: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if resource:
            details['resource'] = resource
        if action:
            details['action'] = action
        if user_id:
            details['user_id'] = user_id
        
        super().__init__(message, details=details, **kwargs)


class BusinessRuleError(BaseApplicationError):
    """Raised when business rules are violated"""
    
    def __init__(
        self,
        message: str,
        rule: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if rule:
            details['rule'] = rule
        if context:
            details['context'] = context
        
        super().__init__(message, details=details, **kwargs)


class ConfigurationError(BaseApplicationError):
    """Raised when configuration is invalid or missing"""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if config_key:
            details['config_key'] = config_key
        if config_value is not None:
            details['config_value'] = str(config_value)
        
        super().__init__(message, details=details, **kwargs)


class ExternalServiceError(BaseApplicationError):
    """Raised when external service calls fail"""
    
    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if service:
            details['service'] = service
        if endpoint:
            details['endpoint'] = endpoint
        if status_code:
            details['status_code'] = status_code
        if response_data:
            details['response_data'] = response_data
        
        super().__init__(message, details=details, **kwargs)


class RateLimitError(BaseApplicationError):
    """Raised when rate limits are exceeded"""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: Optional[int] = None,
        window: Optional[str] = None,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if limit:
            details['limit'] = limit
        if window:
            details['window'] = window
        if retry_after:
            details['retry_after'] = retry_after
        
        super().__init__(message, details=details, **kwargs)


# HTTP Status Code Mapping for API responses
EXCEPTION_STATUS_MAP = {
    NotFoundError: HTTPStatus.NOT_FOUND,
    ValidationError: HTTPStatus.BAD_REQUEST,
    AuthenticationError: HTTPStatus.UNAUTHORIZED,
    AuthorizationError: HTTPStatus.FORBIDDEN,
    BusinessRuleError: HTTPStatus.CONFLICT,
    ConfigurationError: HTTPStatus.INTERNAL_SERVER_ERROR,
    ExternalServiceError: HTTPStatus.BAD_GATEWAY,
    RateLimitError: HTTPStatus.TOO_MANY_REQUESTS,
    DatabaseError: HTTPStatus.INTERNAL_SERVER_ERROR,
    BaseApplicationError: HTTPStatus.INTERNAL_SERVER_ERROR,
}


def get_http_status(exception: BaseApplicationError) -> HTTPStatus:
    """Get HTTP status code for exception type"""
    return EXCEPTION_STATUS_MAP.get(
        type(exception), 
        HTTPStatus.INTERNAL_SERVER_ERROR
    )


def handle_exception_chain(exception: Exception) -> List[Dict[str, Any]]:
    """
    Extract information from exception chain for debugging
    
    Args:
        exception: The exception to analyze
        
    Returns:
        List of exception information dictionaries
    """
    chain = []
    current = exception
    
    while current is not None:
        if isinstance(current, BaseApplicationError):
            chain.append(current.to_dict())
        else:
            chain.append({
                "error": current.__class__.__name__,
                "message": str(current),
                "type": current.__class__.__name__
            })
        
        # Move to the next exception in the chain
        if hasattr(current, 'cause'):
            current = current.cause
        elif hasattr(current, '__cause__'):
            current = current.__cause__
        elif hasattr(current, '__context__'):
            current = current.__context__
        else:
            current = None
    
    return chain


# Context manager for exception handling
class ExceptionHandler:
    """Context manager for standardized exception handling"""
    
    def __init__(
        self,
        operation: str,
        logger,
        reraise: bool = True,
        default_exception: type = BaseApplicationError
    ):
        self.operation = operation
        self.logger = logger
        self.reraise = reraise
        self.default_exception = default_exception
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False
        
        # Log the exception with context
        self.logger.error(
            f"Exception in {self.operation}: {exc_val}",
            extra={
                'operation': self.operation,
                'exception_type': exc_type.__name__,
                'exception_chain': handle_exception_chain(exc_val)
            }
        )
        
        # Re-raise as application exception if it's not already one
        if self.reraise and not isinstance(exc_val, BaseApplicationError):
            raise self.default_exception(
                f"Error in {self.operation}: {str(exc_val)}",
                cause=exc_val
            )
        
        return not self.reraise