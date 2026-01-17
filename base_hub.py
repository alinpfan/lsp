from usys import stdin, stdout

print("ready")

while True:
    line = stdin.readline()          
    if not line:
        continue
    stdout.write("hub: " + line)    