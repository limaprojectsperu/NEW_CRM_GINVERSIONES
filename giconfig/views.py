from django.http import HttpResponse
from django.shortcuts import render

def home_view(request):
    """
    Vista simple para la página principal.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Grupo Imagen SAC</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background-color: #f5f5f5;
            }
            .container {
                text-align: center;
            }
            h1 {
                font-size: 3rem;
                color: #333;
                margin-bottom: 1rem;
            }
            p {
                font-size: 1.2rem;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Grupo Imagen SAC 2</h1>
            <p>Bienvenido a nuestro sitio web</p>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html_content)