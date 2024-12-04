import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_interventii, adauga_interventie, is_sef_birou, aproba_interventie

# Lista personal IT
PERSONAL_IT = [
    'constantin.dragomir',
    'corina.cervinschi',
    'virgil.ionita',
    'andrei.barbu',
    'valentin.ene',
    'gabriel.mertea',
    'valentin.dinu',
    'laurentiu.henegariu'
]

def show_interventii_page():
    st.title("Registrul Intervențiilor IT")
    
    # CSS pentru formularul de intervenție
    st.markdown("""
    <style>
        /* Stiluri pentru formularul de intervenție */
        div[data-testid="stForm"] {
            background-color: #f8f9fa;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
            max-width: 1200px !important;
            margin-left: auto;
            margin-right: auto;
        }
        
        /* Stiluri pentru câmpurile de input */
        div.row-widget.stTextInput > div > div > input {
            min-height: 45px;
            font-size: 16px;
        }
        
        /* Stiluri pentru textarea */
        div.row-widget.stTextArea > div > div > textarea {
            min-height: 100px !important;
            font-size: 16px;
        }
        
        /* Stiluri pentru butonul de submit */
        div[data-testid="stForm"] button[type="submit"] {
            width: 300px;
            height: 46px;
            margin: 0 auto;
            display: block;
            font-size: 16px;
        }

        /* Ajustare pentru containerul principal */
        .block-container {
            max-width: 1400px;
            padding-left: 5rem;
            padding-right: 5rem;
        }

        /* Stiluri pentru butonul de anulare */
        .stButton button {
            width: 100%;
            margin-top: 1rem;
        }
        
        /* Stilizare pentru butoanele de number input */
        .stNumberInput button {
            width: 3rem !important;
            height: 2rem !important;
            font-size: 1.2rem !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Inițializare variabilă de sesiune pentru formularul de adăugare
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
                # Setăm valoarea implicită în funcție de utilizatorul conectat
                default_index = PERSONAL_IT.index(st.session_state['username']) if st.session_state['username'] in PERSONAL_IT else 0
                personal = st.selectbox(
                    "👨‍💻 Personal ITC",
                    options=PERSONAL_IT,
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
            df['Ora'] = pd.to_datetime(df['Ora'], format='mixed').dt.strftime('%H:%M')
            
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
                personal_it_options = ['Toate'] + PERSONAL_IT
                personal_filter = st.selectbox(
                    "Personal IT",
                    options=personal_it_options,
                    index=0  # Setăm mereu 'Toate' ca opțiune implicită
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
            if personal_filter != 'Toate':
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
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_aprobate = len(df[df['Status'] == 'Aprobat'])
                st.metric("✅ Intervenții Aprobate", total_aprobate)
            
            with col2:
                total_respinse = len(df[df['Status'] == 'Respins'])
                st.metric("❌ Intervenții Respinse", total_respinse)
            
            with col3:
                total_asteptare = len(df[df['Status'] == 'In Asteptare'])
                st.metric("⏳ Intervenții în Așteptare", total_asteptare)
            
            # Dacă este virgil.ionita, afișăm secțiunea de aprobare
            if st.session_state['username'] == 'virgil.ionita':
                st.markdown("---")
                st.markdown("### 📋 Aprobare Intervenții")
                st.markdown("Selectați intervențiile pe care doriți să le procesați:")
                
                # Filtrăm doar intervențiile în așteptare (verificăm ambele variante posibile)
                interventii_asteptare = df[df['Status'].isin(['In Asteptare', 'In asteptare', 'in asteptare'])]
                
                if not interventii_asteptare.empty:
                    for _, row in interventii_asteptare.iterrows():
                        with st.container():
                            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                            with col1:
                                st.markdown(f"**Intervenția #{row['Nr.']}** din {row['Data']}")
                                st.markdown(f"Personal IT: **{row['Personal IT']}**")
                            with col2:
                                st.markdown(f"Solicitant: **{row['Solicitant']}**")
                                st.markdown(f"Solicitare: {row['Solicitare'][:100]}...")
                            with col3:
                                if st.button("✅ Aprobă", key=f"approve_{row['Nr.']}"):
                                    if aproba_interventie(row['Nr.'], st.session_state['username'], 'Aprobat'):
                                        st.success(f"✅ Intervenția #{row['Nr.']} a fost aprobată!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Eroare la aprobarea intervenției!")
                            with col4:
                                if st.button("❌ Respinge", key=f"reject_{row['Nr.']}"):
                                    if aproba_interventie(row['Nr.'], st.session_state['username'], 'Respins'):
                                        st.warning(f"❌ Intervenția #{row['Nr.']} a fost respinsă!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Eroare la respingerea intervenției!")
                            st.markdown("---")
                else:
                    st.info("👍 Nu există intervenții în așteptare de procesare.")
        else:
            st.info("Nu există intervenții înregistrate.")
