import typer

app = typer.Typer()

@app.command()
def hello(nombre: str):
    typer.echo(f'Hello {nombre}')
    
    
if __name__ == '__main__':
    app()