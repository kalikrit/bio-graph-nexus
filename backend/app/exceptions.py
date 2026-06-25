"""Custom exceptions for the application."""


class AppException(Exception):
    """Базовое исключение приложения."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NlpProcessingError(AppException):
    """Ошибка при обработке текста в NLP-пайплайне."""

    def __init__(self, detail: str = "NLP processing error"):
        super().__init__(message=detail, status_code=500)


class Neo4jConnectionError(AppException):
    """Ошибка подключения или выполнения запроса к Neo4j."""

    def __init__(self, detail: str = "Database connection error"):
        super().__init__(message=detail, status_code=500)


class EmptyTextError(AppException):
    """Текст запроса пуст или содержит только пробелы."""

    def __init__(self):
        super().__init__(message="Text must not be empty", status_code=422)