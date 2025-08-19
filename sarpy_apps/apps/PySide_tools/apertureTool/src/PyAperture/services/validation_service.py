class ValidationService:
    """
    Service class for handling input validation.
    
    This class provides static methods for validating and sanitizing user input
    values, ensuring they fall within acceptable ranges and types.
    """
    
    @staticmethod
    def ensure_valid_integer(value: str, minimum: int = 1) -> int:
        """
        Ensure value is a valid integer within bounds.
        
        This method converts a string value to an integer and ensures it meets
        the minimum requirement. If conversion fails, returns the minimum value.
        
        Args:
            value: String value to convert and validate
            minimum: Minimum acceptable integer value
            
        Returns:
            Validated integer value, guaranteed to be >= minimum
        """
        try:
            int_value = int(value)
            return max(minimum, int_value)
        except (ValueError, TypeError):
            print(f'Invalid value, setting to {minimum}')
            return minimum
    
    @staticmethod
    def ensure_valid_percentage(value: str, minimum: float = 0.01, maximum: float = 1.0) -> float:
        """
        Ensure value is a valid percentage between min and max.
        
        This method converts a string value to a float and ensures it falls within
        the specified range. If conversion fails, returns a default value of 0.5.
        
        Args:
            value: String value to convert and validate
            minimum: Minimum acceptable percentage value
            maximum: Maximum acceptable percentage value
            
        Returns:
            Validated float value, guaranteed to be between minimum and maximum
        """
        try:
            float_value = float(value)
            return max(minimum, min(maximum, float_value))
        except (ValueError, TypeError):
            print('Invalid value, setting to 0.5')
            return 0.5