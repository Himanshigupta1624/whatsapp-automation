from django.db import models

class MessageLog(models.Model):
    source=models.CharField(max_length=20,default='Whatsapp')
    raw_text=models.TextField()
    is_relevant=models.BooleanField(default=False)
    forwarded_to_telegram=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)