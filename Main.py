# DJEN Downloader Android (Kivy)

```python
import os
import json
import math
import time
import threading
import requests
import datetime
import xml.etree.ElementTree as ET

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock

# =========================================================
# ANDROID DOWNLOAD PATH
# =========================================================

try:
    from android.storage import primary_external_storage_path

    BASE_PATH = os.path.join(
        primary_external_storage_path(),
        "Download",
        "DJEN"
    )

except:

    BASE_PATH = os.path.join(
        os.getcwd(),
        "DJEN"
    )

JSON_TRIBUNAIS = os.path.join(BASE_PATH, "tribunal.json")
PASTA_SALVAR = os.path.join(BASE_PATH, "jsonsSalvos")
XML_FALHOS = os.path.join(BASE_PATH, "falhos.xml")

os.makedirs(PASTA_SALVAR, exist_ok=True)

# =========================================================
# APP
# =========================================================

class DJENLayout(BoxLayout):

    def __init__(self, **kwargs):

        super().__init__(orientation='vertical', **kwargs)

        self.spacing = 10
        self.padding = 10

        self.checkboxes_tribunais = {}

        # =====================================================
        # DATA INICIO
        # =====================================================

        self.add_widget(Label(text='Data Início (YYYY-MM-DD)'))

        self.data_inicio = TextInput(
            text=datetime.date.today().strftime('%Y-%m-%d'),
            size_hint_y=None,
            height=50
        )

        self.add_widget(self.data_inicio)

        # =====================================================
        # DATA FIM
        # =====================================================

        self.add_widget(Label(text='Data Fim (YYYY-MM-DD)'))

        self.data_fim = TextInput(
            text=datetime.date.today().strftime('%Y-%m-%d'),
            size_hint_y=None,
            height=50
        )

        self.add_widget(self.data_fim)

        # =====================================================
        # HORARIO
        # =====================================================

        self.add_widget(Label(text='Agendamento (HH:MM)'))

        self.horario = TextInput(
            hint_text='Ex: 23:30',
            size_hint_y=None,
            height=50
        )

        self.add_widget(self.horario)

        # =====================================================
        # BOTAO AGENDAR
        # =====================================================

        btn_agendar = Button(
            text='AGENDAR DOWNLOAD',
            size_hint_y=None,
            height=60
        )

        btn_agendar.bind(on_press=self.agendar_download)

        self.add_widget(btn_agendar)

        # =====================================================
        # LISTA TRIBUNAIS
        # =====================================================

        self.add_widget(Label(text='Tribunais'))

        scroll = ScrollView(size_hint=(1, 1))

        self.grid_tribunais = GridLayout(
            cols=1,
            spacing=5,
            size_hint_y=None
        )

        self.grid_tribunais.bind(
            minimum_height=self.grid_tribunais.setter('height')
        )

        tribunais = self.carregar_tribunais()

        for tribunal in tribunais:

            linha = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=50
            )

            chk = CheckBox(size_hint_x=None, width=60)

            lbl = Label(
                text=tribunal,
                halign='left'
            )

            linha.add_widget(chk)
            linha.add_widget(lbl)

            self.grid_tribunais.add_widget(linha)

            self.checkboxes_tribunais[tribunal] = chk

        scroll.add_widget(self.grid_tribunais)

        self.add_widget(scroll)

        # =====================================================
        # BOTAO DOWNLOAD
        # =====================================================

        btn_download = Button(
            text='INICIAR DOWNLOAD',
            size_hint_y=None,
            height=70
        )

        btn_download.bind(on_press=self.iniciar_download)

        self.add_widget(btn_download)

        # =====================================================
        # LOG
        # =====================================================

        self.log_box = TextInput(
            readonly=True,
            size_hint=(1, 1)
        )

        self.add_widget(self.log_box)

        self.log('Sistema iniciado.')

    # =========================================================
    # LOG
    # =========================================================

    def log(self, texto):

        agora = datetime.datetime.now().strftime('%H:%M:%S')

        mensagem = f'[{agora}] {texto}\n'

        def atualizar(dt):
            self.log_box.text += mensagem

        Clock.schedule_once(atualizar)

    # =========================================================
    # POPUP
    # =========================================================

    def popup(self, titulo, mensagem):

        box = BoxLayout(orientation='vertical', padding=10)

        box.add_widget(Label(text=mensagem))

        btn = Button(
            text='OK',
            size_hint_y=None,
            height=50
        )

        popup = Popup(
            title=titulo,
            content=box,
            size_hint=(0.8, 0.4)
        )

        btn.bind(on_press=popup.dismiss)

        box.add_widget(btn)

        popup.open()

    # =========================================================
    # TRIBUNAIS
    # =========================================================

    def carregar_tribunais(self):

        try:

            with open(JSON_TRIBUNAIS, 'r', encoding='utf-8') as f:

                dados = json.load(f)

                return dados.get('tribunais', [])

        except Exception as e:

            self.popup(
                'Erro',
                f'Erro ao carregar tribunal.json:\n{e}'
            )

            return []

    # =========================================================
    # URL
    # =========================================================

    def construir_url(
        self,
        tribunal,
        inicio,
        fim,
        pagina,
        itens
    ):

        return (
            f'https://comunicaapi.pje.jus.br/api/v1/comunicacao?'
            f'pagina={pagina}'
            f'&itensPorPagina={itens}'
            f'&siglaTribunal={tribunal}'
            f'&dataDisponibilizacaoInicio={inicio}'
            f'&dataDisponibilizacaoFim={fim}'
        )

    # =========================================================
    # DOWNLOAD JSON
    # =========================================================

    def baixar_json(self, url, tentativa=1):

        try:

            response = requests.get(
                url,
                timeout=30
            )

            response.raise_for_status()

            return response.json()

        except Exception as e:

            self.log(
                f'Erro tentativa {tentativa}: {e}'
            )

            if tentativa < 3:

                time.sleep(10)

                return self.baixar_json(
                    url,
                    tentativa + 1
                )

            return None

    # =========================================================
    # XML FALHOS
    # =========================================================

    def salvar_falhos_xml(self, lista_falhos):

        root = ET.Element('falhos')

        for link in lista_falhos:

            item = ET.SubElement(root, 'link')

            item.text = link

        tree = ET.ElementTree(root)

        tree.write(
            XML_FALHOS,
            encoding='utf-8',
            xml_declaration=True
        )

    def carregar_falhos_xml(self):

        if not os.path.exists(XML_FALHOS):
            return []

        tree = ET.parse(XML_FALHOS)

        root = tree.getroot()

        return [
            item.text
            for item in root.findall('link')
        ]

    # =========================================================
    # DOWNLOAD
    # =========================================================

    def iniciar_download(self, instance):

        threading.Thread(
            target=self.processar_download,
            daemon=True
        ).start()

    def processar_download(self):

        tribunais = []

        for tribunal, chk in self.checkboxes_tribunais.items():

            if chk.active:
                tribunais.append(tribunal)

        if not tribunais:

            self.popup(
                'Aviso',
                'Selecione pelo menos um tribunal.'
            )

            return

        data_inicio = self.data_inicio.text.strip()
        data_fim = self.data_fim.text.strip()

        total_salvos = 0

        for tribunal in tribunais:

            self.log(f'INICIANDO -> {tribunal}')

            url_count = self.construir_url(
                tribunal,
                data_inicio,
                data_fim,
                1,
                6
            )

            dados_count = self.baixar_json(url_count)

            if not dados_count:

                self.log(
                    f'Erro COUNT -> {tribunal}'
                )

                continue

            count = dados_count.get('count', 0)

            total_paginas = math.ceil(count / 100)

            self.log(
                f'{tribunal} -> {count} registros'
            )

            self.log(
                f'{tribunal} -> {total_paginas} páginas'
            )

            pasta_destino = os.path.join(
                PASTA_SALVAR,
                tribunal,
                f'{data_inicio}_{data_fim}'
            )

            os.makedirs(
                pasta_destino,
                exist_ok=True
            )

            falhos = []

            for pagina in range(1, total_paginas + 1):

                url = self.construir_url(
                    tribunal,
                    data_inicio,
                    data_fim,
                    pagina,
                    100
                )

                self.log(
                    f'BAIXANDO -> {tribunal} página {pagina}'
                )

                dados = self.baixar_json(url)

                if dados is not None:

                    nome_arquivo = os.path.join(
                        pasta_destino,
                        f'{tribunal}_{pagina:05d}.json'
                    )

                    with open(nome_arquivo, 'w', encoding='utf-8') as f:

                        json.dump(
                            dados,
                            f,
                            ensure_ascii=False,
                            indent=2
                        )

                    qtd = len(
                        dados.get('items', [])
                    )

                    self.log(
                        f'SALVO -> página {pagina} ({qtd} itens)'
                    )

                    total_salvos += 1

                else:

                    falhos.append(url)

                    self.log(
                        f'FALHOU -> página {pagina}'
                    )

                time.sleep(0.3)

            if falhos:

                self.salvar_falhos_xml(falhos)

                self.log(
                    f'{len(falhos)} links falharam.'
                )

        self.popup(
            'Concluído',
            f'Download finalizado.\nArquivos: {total_salvos}'
        )

    # =========================================================
    # AGENDAMENTO
    # =========================================================

    def agendar_download(self, instance):

        horario = self.horario.text.strip()

        try:

            hora = datetime.datetime.strptime(
                horario,
                '%H:%M'
            ).time()

        except:

            self.popup(
                'Erro',
                'Formato inválido. Use HH:MM'
            )

            return

        self.log(
            f'Agendado para {horario}'
        )

        def esperar():

            while True:

                agora = datetime.datetime.now().time()

                if (
                    agora.hour == hora.hour
                    and
                    agora.minute == hora.minute
                ):

                    self.log(
                        'HORÁRIO ATINGIDO -> iniciando'
                    )

                    threading.Thread(
                        target=self.processar_download,
                        daemon=True
                    ).start()

                    break

                time.sleep(20)

        threading.Thread(
            target=esperar,
            daemon=True
        ).start()

# =========================================================
# APP
# =========================================================

class DJENApp(App):

    def build(self):

        return DJENLayout()

# =========================================================
# START
# =========================================================

if __name__ == '__main__':

    DJENApp().run()
```

---

# COMO GERAR O APK

## 1. Instalar Ubuntu/Linux

O Buildozer funciona oficialmente no Linux.

---

## 2. Instalar dependências

```bash
sudo apt update
sudo apt install -y python3-pip git zip unzip openjdk-17-jdk
pip install buildozer cython
```

---

# 3. Criar projeto

```bash
buildozer init
```

---

# 4. Editar buildozer.spec

Troque:

```ini
source.include_exts = py,png,jpg,kv,json,xml
requirements = python3,kivy,requests
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
```

---

# 5. Gerar APK

```bash
buildozer android debug
```

---

# APK FINAL

O APK será gerado em:

```bash
bin/
```

Exemplo:

```bash
bin/djenapp-0.1-arm64-v8a-debug.apk
```

---

# NO ANDROID

Os JSONs serão salvos em:

```text
Download/DJEN/jsonsSalvos/
```

Exemplo:

```text
/storage/emulated/0/Download/DJEN/jsonsSalvos/TJRS/2026-05-07_2026-05-07/
```
