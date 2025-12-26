from ine.main import Client

client = Client()
operaciones = client.get_operaciones()
print(operaciones)
