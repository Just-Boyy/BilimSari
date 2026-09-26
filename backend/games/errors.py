# -*- coding: utf-8 -*-
"""O'yin tizimi xatolari — foydalanuvchiga tushunarli o'zbekcha matn bilan."""


class GameError(Exception):
    def __init__(self, code: str, message: str, http_status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
