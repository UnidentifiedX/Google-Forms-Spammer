import requests

new_link = "https://docs.google.com/forms/u/0/d/e/1FAIpQLSfu2uunPNVUSgXPuNIpf2uJ7S6JX2IgPDM-NgAyISZH9GfoJw/formResponse"
data = {
    "entry.1682841415": "it's morbin time",
    "entry.1852729875": "c"
}
response = requests.post(new_link, data=data)

print(response)