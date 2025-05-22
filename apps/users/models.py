from django.db import models

# Create your models here.

class Marca(models.Model):
    nombre = models.CharField(max_length=200, null=True, blank=True)
    estado = models.BooleanField(default=True) 

    class Meta:
        db_table = 'marcas'
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'

    def __str__(self):
        return f"Marca {self.id}: {self.nombre}"