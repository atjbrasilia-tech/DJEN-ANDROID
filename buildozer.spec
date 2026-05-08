[app]

# Título
 title = DJEN Downloader

# Nome do pacote
 package.name = djen

# Domínio
 package.domain = org.djen

# Arquivo principal
 source.dir = .
 source.include_exts = py,png,jpg,kv,json,xml

# Versão
 version = 1.0

# Requisitos
 requirements = python3,kivy,requests

# Orientação
 orientation = portrait

# Permissões Android
 android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE

# API Android
 android.api = 33
 android.minapi = 24
 android.ndk = 25b

# Arquitetura
 android.archs = arm64-v8a

# Tela cheia
 fullscreen = 0

[buildozer]
 log_level = 2
 warn_on_root = 1