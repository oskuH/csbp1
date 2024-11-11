from django.db import models

class Cookies(models.Model):
    cookies = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Cookie stolen at {self.timestamp}'