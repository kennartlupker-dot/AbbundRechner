import math
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton

class AbbundApp(App):
    def build(self):
        self.title = "Abbund-Rechner Profi"
        self.is_grat = True # Standardauswahl

        # Hauptlayout (Scrollbar, damit alles aufs Handydisplay passt)
        root = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 1. Sparrenart-Auswahl (Grat / Kehle)
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.btn_grat = ToggleButton(text="Gratsparren", group="typ", state="down")
        self.btn_kehle = ToggleButton(text="Kehlsparren", group="typ")
        self.btn_grat.bind(on_press=self.set_grat)
        self.btn_kehle.bind(on_press=self.set_kehle)
        btn_layout.add_widget(self.btn_grat)
        btn_layout.add_widget(self.btn_kehle)
        root.add_widget(btn_layout)

        # 2. Eingabefelder im Gitter
        grid = GridLayout(cols=2, spacing=10, size_hint_y=None, height=200)
        
        grid.add_widget(Label(text="Neigung Hauptdach (°):"))
        self.input_alpha_h = TextInput(text="38", input_filter="float", multiline=False)
        grid.add_widget(self.input_alpha_h)

        grid.add_widget(Label(text="Neigung Nebendach (°):"))
        self.input_alpha_n = TextInput(text="38", input_filter="float", multiline=False)
        grid.add_widget(self.input_alpha_n)

        grid.add_widget(Label(text="Sparrenbreite (cm):"))
        self.input_g = TextInput(text="8", input_filter="float", multiline=False)
        grid.add_widget(self.input_g)

        grid.add_widget(Label(text="Traufwinkel (°):"))
        self.input_w_ecke = TextInput(text="90", input_filter="float", multiline=False)
        grid.add_widget(self.input_w_ecke)
        
        root.add_widget(grid)

        # 3. Berechnen-Knopf
        calc_btn = Button(text="BERECHNEN", size_hint_y=None, height=60, background_color=(0, 0.6, 0, 1))
        calc_btn.bind(on_press=self.berechne)
        root.add_widget(calc_btn)

        # 4. Ergebnisanzeige (Scrollbar)
        scroll = ScrollView()
        self.output_label = Label(text="Ergebnisse erscheinen hier...", size_hint_y=None, halign="left", valign="top")
        self.output_label.bind(texture_size=self.output_label.setter('size'))
        scroll.add_widget(self.output_label)
        root.add_widget(scroll)

        return root

    def set_grat(self, instance):
        self.is_grat = True
        self.btn_kehle.state = "normal"

    def set_kehle(self, instance):
        self.is_grat = False
        self.btn_grat.state = "normal"

    def berechne(self, instance):
        try:
            alpha_h = float(self.input_alpha_h.text)
            alpha_n = float(self.input_alpha_n.text)
            g = float(self.input_g.text)
            w_ecke = float(self.input_w_ecke.text)
        except ValueError:
            self.output_label.text = "⚠️ Bitte alle Felder korrekt ausfüllen!"
            return

        alpha_h_rad, alpha_n_rad = math.radians(alpha_h), math.radians(alpha_n)
        w_ecke_rad = math.radians(w_ecke)

        # Grundwinkel
        zaehler_phi = math.sin(w_ecke_rad)
        nenner_phi = (math.tan(alpha_h_rad) / math.tan(alpha_n_rad)) + math.cos(w_ecke_rad)
        phi_h_rad = math.atan2(zaehler_phi, nenner_phi)
        phi_n_rad = w_ecke_rad - phi_h_rad

        # Raum- und Maschinenwinkel
        epsilon_rad = math.atan(math.tan(alpha_h_rad) * math.sin(phi_h_rad))
        mw_h_rad = math.atan(math.sin(epsilon_rad) / math.tan(phi_h_rad))
        mw_n_rad = math.atan(math.sin(epsilon_rad) / math.tan(phi_n_rad))

        # Wahrer Schnittwinkel
        wahr_hd = math.degrees(math.atan(1.0 / (math.cos(alpha_h_rad) * math.tan(phi_h_rad)))) if phi_h_rad != 0 else 0
        wahr_nd = math.degrees(math.atan(1.0 / (math.cos(alpha_n_rad) * math.tan(phi_n_rad)))) if phi_n_rad != 0 else 0

        def berechne_risse(d_hd, d_nd):
            h_hd = - d_hd * (math.tan(alpha_h_rad) * math.cos(phi_h_rad) / math.sin(phi_h_rad) if phi_h_rad != 0 else 0)
            h_nd = - d_nd * (math.tan(alpha_n_rad) * math.cos(phi_n_rad) / math.sin(phi_n_rad) if phi_n_rad != 0 else 0)
            h_max = max(h_hd, 0.0, h_nd)
            return h_max - h_hd, h_max, h_max - h_nd

        tan_h, tan_n = math.tan(mw_h_rad), math.tan(mw_n_rad)
        lbl_lin = "Gratlinie" if self.is_grat else "Kehllinie"
        lbl_ris = "Riss"

        # Option 1
        opt1_text = ""
        if (tan_h + tan_n) != 0:
            abstand_hd_opt1 = g * (tan_n / (tan_h + tan_n))
            if 0 <= abstand_hd_opt1 <= g:
                p_hd1, p_lin1, p_nd1 = berechne_risse(abstand_hd_opt1, g - abstand_hd_opt1)
                opt1_text = f"\n[OPTION 1] " + ("Kantenbündig" if self.is_grat else "Flankenrisse bei 0") + \
                            f"\nLage {lbl_lin}: {abstand_hd_opt1:.2f} cm ab HD" \
                            f"\n-> {lbl_ris} HD: {p_hd1:.2f} cm | {lbl_lin}: {p_lin1:.2f} cm | ND: {p_nd1:.2f} cm\n"

        # Option 2
        p_hd2, p_lin2, p_nd2 = berechne_risse(g/2.0, g/2.0)

        # Option 3
        cos_h, cos_n = abs(math.cos(mw_h_rad)), abs(math.cos(mw_n_rad))
        abstand_hd_opt3 = g * (cos_h / (cos_h + cos_n))
        p_hd3, p_lin3, p_nd3 = berechne_risse(abstand_hd_opt3, g - abstand_hd_opt3)

        # Textausgabe zusammenbauen
        res = f"WINKEL & PROFILE:\n" \
              f"-----------------------------------------\n" \
              f"Raumwinkel: {abs(math.degrees(epsilon_rad)):.2f}°\n" \
              f"Grundwinkel: HD = {math.degrees(phi_h_rad):.2f}° | ND = {math.degrees(phi_n_rad):.2f}°\n" \
              f"Maschinenwinkel: HD = {math.degrees(mw_h_rad):.2f}° | ND = {math.degrees(mw_n_deg if 'mw_n_deg' in locals() else math.degrees(mw_n_rad)):.2f}°\n" \
              f"Schnittwinkel Dachhaut: HD = {abs(wahr_hd):.2f}° | ND = {abs(wahr_nd):.2f}°\n"
              
        if math.degrees(phi_h_rad) > 90.0 or math.degrees(phi_n_rad) > 90.0:
            res += "⚠️ Sonderfall: Winkel > 90°!\n"
            
        res += f"\nMaße gemessen ab Holzoberkante:\n" \
               f"========================================="
               
        if opt1_text:
            res += opt1_text
            
        res += f"\n[OPTION 2] Mitte Holz\n" \
               f"Lage {lbl_lin}: {g/2.0:.2f} cm ab HD\n" \
               f"-> {lbl_ris} HD: {p_hd2:.2f} cm | {lbl_lin}: {p_lin2:.2f} cm | ND: {p_nd2:.2f} cm\n"
               
        res += f"\n[OPTION 3] " + ("Gleiche Breite" if self.is_grat else "Gleicher Schifter-Versatz") + \
               f"\nLage {lbl_lin}: {abstand_hd_opt3:.2f} cm ab HD\n" \
               f"-> {lbl_ris} HD: {p_hd3:.2f} cm | {lbl_lin}: {p_lin3:.2f} cm | ND: {p_nd3:.2f} cm\n"
               
        if not self.is_grat:
            res += f"   (Kehle um {p_lin3:.2f} cm tiefer/hoch setzen)\n"

        self.output_label.text = res

if __name__ == '__main__':
    AbbundApp().run()
