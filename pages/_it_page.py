import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import (
    get_interventii, 
    adauga_interventie, 
    is_sef_birou,
    is_it_personal, 
    aproba_interventie,
    get_personal_it,
    normalize_username
)

# Lista personal IT
PERSONAL_IT = get_personal_it()

def show_interventii_page():
    # Verificăm dacă utilizatorul este autentificat
    if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
        st.warning("Trebuie să te autentifici pentru a accesa această pagină.")
        st.stop()
        return

    # Verificăm dacă utilizatorul face parte din serviciul IT
    current_user = st.session_state.get('username', '')
    if not is_it_personal(current_user):
        st.error("Acces interzis! Doar personalul IT poate accesa această pagină.")
        st.stop()
        return

    st.title("Registrul Intervențiilor IT")
    
    # CSS pentru formularul de intervenție
    st.markdown("""
    <style>
        /* Stiluri pentru formularul de intervenție */
        div[data-testid="stForm"] {
            background-color: #0e1117;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            margin-bottom: 1.5rem;
            max-width: 800px !important;
            margin-left: auto;
            margin-right: auto;
        }
        
        /* Stiluri pentru câmpurile de input */
        div.row-widget.stTextInput > div > div > input {
            background-color: #262730;
            border: 1px solid #464855;
            border-radius: 4px;
            padding: 0.5rem;
            font-size: 14px;
            width: 100%;
            color: white;
        }
        
        /* Stiluri pentru textarea */
        div.row-widget.stTextArea > div > div > textarea {
            background-color: #262730;
            border: 1px solid #464855;
            border-radius: 4px;
            padding: 0.5rem;
            font-size: 14px;
            min-height: 100px !important;
            color: white;
        }
        
        /* Stiluri pentru butonul de submit */
        div[data-testid="stForm"] button[type="submit"] {
            width: 200px;
            margin: 1rem auto;
            display: block;
        }

        /* Ajustare pentru containerul principal */
        .block-container {
            max-width: 1200px;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* Stiluri pentru selectbox */
        div.row-widget.stSelectbox > div > div {
            background-color: #262730;
            border: 1px solid #464855;
            border-radius: 4px;
            color: white;
        }
        
        /* Stiluri pentru number input */
        div.row-widget.stNumberInput > div > div > input {
            background-color: #262730;
            border: 1px solid #464855;
            border-radius: 4px;
            padding: 0.5rem;
            font-size: 14px;
            color: white;
        }
        
        /* Stiluri pentru etichete */
        label {
            color: #fafafa;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Inițializăm starea formularului dacă nu există
    if 'show_add_form' not in st.session_state:
        st.session_state['show_add_form'] = False
    
    # Afișare formular sau buton de adăugare
    if not st.session_state['show_add_form']:
        # Buton pentru adăugare intervenție nouă
        if st.button("➕ Adaugă Intervenție Nouă", type="primary", use_container_width=True):
            st.session_state['show_add_form'] = True
            st.rerun()
    else:
        # Buton pentru anulare
        if st.button("❌ Am greșit, nu vreau o intervenție nouă", type="secondary", use_container_width=True):
            st.session_state['show_add_form'] = False
            st.rerun()
    
    # Formular pentru adăugare intervenție
    if st.session_state['show_add_form']:
        with st.form("add_intervention_form"):
            st.subheader("📝 Adaugă Intervenție Nouă")
            st.markdown("---")
            
            # Prima linie: Data și Ora
            col1, col2 = st.columns(2)
            with col1:
                data = st.date_input(
                    "📅 Data",
                    value=datetime.now().date(),
                    key="data_interventie"
                )
            with col2:
                # Generăm opțiunile pentru oră pornind de la ora curentă
                now = datetime.now()
                current_time = now.replace(minute=(now.minute // 15) * 15, second=0, microsecond=0)
                time_options = []
                
                # Adăugăm opțiuni pentru următoarele 24 de ore, la fiecare 15 minute
                for i in range(96):  # 24 ore * 4 (15 minute intervale)
                    time = current_time + timedelta(minutes=15 * i)
                    time_str = time.strftime("%H:%M")
                    time_options.append(time_str)
                
                # Găsim indexul orei curente în lista de opțiuni
                current_time_str = current_time.strftime("%H:%M")
                default_time_index = time_options.index(current_time_str)
                
                ora = st.selectbox(
                    "🕐 Ora",
                    options=time_options,
                    index=default_time_index,
                    key="ora_interventie"
                )
            
            # A doua linie: Solicitant și Personal IT
            col1, col2 = st.columns(2)
            with col1:
                solicitant = st.text_input(
                    "👤 Solicitant",
                    placeholder="Numele solicitantului",
                    key="solicitant_interventie"
                )
            with col2:
                # Obținem lista personalului IT din baza de date
                personal_it_list = get_personal_it()
                if not personal_it_list:
                    st.error("Nu s-a putut obține lista personalului IT")
                    return
                
                # Obținem username-ul normalizat al utilizatorului curent
                current_user = st.session_state.get('username', '')
                normalized_user = normalize_username(current_user)
                
                # Găsim indexul utilizatorului curent în lista
                try:
                    default_index = personal_it_list.index(normalized_user)
                except ValueError:
                    default_index = 0
                    
                personal = st.selectbox(
                    "👨‍💻 Personal ITC",
                    options=personal_it_list,
                    index=default_index,
                    key="personal_interventie"
                )
            
            # A treia linie: Durata
            st.markdown("""
                <style>
                /* Stilizare pentru butoanele de number input */
                .stNumberInput button {
                    width: 4rem !important;
                    height: 2.5rem !important;
                    font-size: 1.5rem !important;
                }
                
                /* Stilizare pentru câmpul de input */
                .stNumberInput input {
                    height: 2.5rem !important;
                    width: 8rem !important;
                    text-align: center !important;
                    font-size: 1.2rem !important;
                }
                
                /* Container pentru number input */
                .stNumberInput > div {
                    display: flex !important;
                    align-items: center !important;
                    gap: 0.5rem !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            durata = st.number_input(
                "⏱️ Durata (minute)",
                min_value=5,
                max_value=480,  # 8 ore
                value=30,
                step=5,
                key="durata_interventie"
            )
            
            # Convertim data în zi
            zile = {
                0: "Luni",
                1: "Marți",
                2: "Miercuri",
                3: "Joi",
                4: "Vineri",
                5: "Sâmbătă",
                6: "Duminică"
            }
            zi = zile[data.weekday()]
            
            # A patra linie: Solicitare și Observații
            solicitare = st.text_area(
                "📋 Solicitare",
                placeholder="Descrierea detaliată a solicitării...",
                key="solicitare_interventie",
                height=120
            )
            
            observatii = st.text_area(
                "📝 Observații",
                placeholder="Observații adiționale (opțional)...",
                key="observatii_interventie",
                height=100
            )
            
            st.markdown("---")
            # Butonul de submit
            submitted = st.form_submit_button(
                "💾 Salvează Intervenția",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                try:
                    if not solicitant or not personal:
                        st.error("❌ Te rog completează toate câmpurile obligatorii!")
                        return
                    
                    # Adăugăm intervenția în baza de date
                    success = adauga_interventie(
                        data_interventie=data,
                        zi=zi,
                        solicitant=solicitant,
                        solicitare=solicitare,
                        ora=ora,
                        durata=durata,
                        personal_itc=personal,
                        observatii=observatii,
                        serviciu_id=1  # Presupunem că avem un serviciu implicit
                    )
                    
                    if success:
                        st.success("✅ Intervenția a fost adăugată cu succes!")
                        st.session_state['show_add_form'] = False
                        st.rerun()
                    else:
                        st.error("❌ A apărut o eroare la adăugarea intervenției!")
                except Exception as e:
                    st.error(f"Eroare la adăugarea intervenției: {str(e)}")
    
    # Afișare tabel cu intervenții doar dacă nu suntem în modul de adăugare
    if not st.session_state['show_add_form']:
        # Afișare tabel intervenții
        st.subheader("Lista Intervențiilor")
        
        # Obținem intervențiile
        interventii = get_interventii()
        
        if interventii:
            # Convertim la DataFrame pentru afișare mai frumoasă
            df = pd.DataFrame(interventii)
            
            # Reordonăm și redenumim coloanele pentru afișare
            columns_order = {
                'NrCrt': 'Nr.',
                'DataInterventie': 'Data',
                'Zi': 'Zi',
                'Solicitant': 'Solicitant',
                'Solicitare': 'Solicitare',
                'Ora': 'Ora',
                'DurataInterventie': 'Durata (min)',
                'PersonalITC': 'Personal IT',
                'Observatii': 'Observații',
                'Status': 'Status'
            }
            
            df = df.rename(columns=columns_order)
            
            # Formatăm ora pentru a afișa doar HH:MM
            df['Ora'] = df['Ora'].apply(lambda x: x.strftime('%H:%M') if pd.notnull(x) else '')
            
            df = df[list(columns_order.values())]
            
            # Adăugăm stilizare pentru status
            def style_status(val):
                if val == 'Aprobat':
                    return 'color: green; font-weight: bold'
                elif val == 'In Asteptare':
                    return 'color: orange; font-weight: bold'
                elif val == 'Respins':
                    return 'color: red; font-weight: bold'
                return ''
            
            # Adăugăm tooltip pentru data aprobării și cine a aprobat/respins
            if 'DataAprobare' in df.columns and 'AprobatDe' in df.columns:
                def format_approval_info(row):
                    if row['Status'] in ['Aprobat', 'Respins'] and pd.notnull(row['DataAprobare']):
                        data_aprobare = pd.to_datetime(row['DataAprobare']).strftime('%d/%m/%Y %H:%M')
                        action = "aprobat" if row['Status'] == 'Aprobat' else "respins"
                        return f"{action} de {row['AprobatDe']} la {data_aprobare}"
                    return row['Status']
                
                df['Status_Info'] = df.apply(format_approval_info, axis=1)
                styled_df = df.style.set_properties(**{'title': df['Status_Info']}, subset=['Status'])
            else:
                styled_df = df.style
            
            # Adăugăm secțiunea de filtre
            st.markdown("### 🔍 Filtre")
            
            # Verificăm și afișăm numele coloanelor pentru debug
            print("Coloane disponibile:", df.columns.tolist())
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Filtru pentru Personal IT
                personal_it_options = ["Toți"] + get_personal_it()
                personal_filter = st.selectbox(
                    "Filtrare după Personal ITC",
                    options=personal_it_options,
                    index=0,
                    key="personal_filter"
                )
            
            with col2:
                # Filtru pentru data
                data_filter = st.date_input(
                    "Data Intervenție",
                    value=None,
                    min_value=pd.to_datetime(df['Data'].min()).date(),
                    max_value=pd.to_datetime(df['Data'].max()).date()
                )
            
            with col3:
                # Filtru pentru căutare text în solicitant și solicitare
                search_text = st.text_input("Caută în solicitant/solicitare", "")
            
            # Aplicăm filtrele
            # 1. Filtru personal IT
            if personal_filter != 'Toți':
                df = df[df['Personal IT'] == personal_filter]
            
            # 2. Filtru dată
            if data_filter is not None:
                df = df[pd.to_datetime(df['Data']).dt.date == data_filter]
            
            # 3. Filtru text
            if search_text:
                search_mask = (
                    df['Solicitant'].str.contains(search_text, case=False, na=False) |
                    df['Solicitare'].str.contains(search_text, case=False, na=False)
                )
                df = df[search_mask]
            
            # Sortăm dataframe-ul descrescător după Nr.
            df = df.sort_values(by='Nr.', ascending=False)
            
            # Adăugăm stilizarea și adăugăm tooltip pentru status
            styled_df = df.style.map(style_status, subset=['Status'])
            
            # Afișăm tabelul
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True  # Dezactivăm indexul automat
            )
            
            # Adăugăm statistici
            st.markdown("### 📊 Statistici")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_interventii = len(df)
                st.metric("📝 Total Intervenții", total_interventii)
            
            with col2:
                total_aprobate = len(df[df['Status'] == 'Aprobat'])
                st.metric("✅ Intervenții Aprobate", total_aprobate)
            
            with col3:
                total_asteptare = len(df[df['Status'] == 'In Asteptare'])
                st.metric("⏳ Intervenții în Așteptare", total_asteptare)
            
            # Dacă este șef de birou, afișăm secțiunea de aprobare
            if is_sef_birou(st.session_state.get('username', '')):
                print(f"DEBUG: Utilizator {st.session_state.get('username')} este șef de birou")
                st.markdown("---")
                st.markdown("### 📋 Aprobare Intervenții")
                st.markdown("Selectați intervențiile pe care doriți să le procesați:")
                
                interventii_asteptare = df[df['Status'].isin(['In Asteptare', 'In asteptare', 'in asteptare'])]
                
                if not interventii_asteptare.empty:
                    for idx, row in interventii_asteptare.iterrows():
                        with st.container():
                            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                            with col1:
                                st.write(f"**Data:** {row['Data']} | **Ora:** {row['Ora']}")
                                st.write(f"**Solicitant:** {row['Solicitant']}")
                            with col2:
                                st.write(f"**Personal IT:** {row['Personal IT']}")
                                st.write(f"**Solicitare:** {row['Solicitare']}")
                            # Afișăm butoanele de aprobare/respingere doar pentru șefii de birou
                            if is_sef_birou(st.session_state.get('username', '')):
                                with col3:
                                    if st.button('✅ Aprobă', key=f'approve_{row["Nr."]}'):
                                        if aproba_interventie(row['Nr.'], st.session_state['username'], 'Aprobat'):
                                            st.success(f"Intervenția #{row['Nr.']} a fost aprobată!")
                                            st.rerun()
                                with col4:
                                    if st.button('❌ Respinge', key=f'reject_{row["Nr."]}'):
                                        if aproba_interventie(row['Nr.'], st.session_state['username'], 'Respins'):
                                            st.error(f"Intervenția #{row['Nr.']} a fost respinsă!")
                                            st.rerun()
                            st.markdown("---")
                else:
                    st.info("Nu există intervenții în așteptare de aprobare.")
        else:
            st.info("Nu există intervenții înregistrate.")
