import csv
import sys

raw_data = """
luxury@kaleidoscope.ru,Ekaterina Volkova,Kaleidoscope Luxury Travel (Moscow),+7-495-123-4567,Russia,Director,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Moscow,CA_CIS_001
private@arthur-ivanov.ru,Arthur Ivanov,Arthur Ivanov Travel Design,+7-495-234-5678,Russia,Founder,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Moscow,CA_CIS_002
vip@luxurytravel.ru,Anastasia Petrova,Luxury Travel Russia,+7-495-345-6789,Russia,VIP Manager,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Moscow,CA_CIS_003
concierge@elitetravel.ru,Dmitry Sokolov,Elite Travel Concierge,+7-495-456-7890,Russia,Concierge Director,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,St. Petersburg,CA_CIS_004
privatejet@skytravel.ru,Olga Ivanova,Sky Travel Premium,+7-495-567-8901,Russia,Private Aviation,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Moscow,CA_CIS_005
yacht@marineluxury.ru,Sergey Volkov,Marine Luxury CIS,+7-495-678-9012,Russia,Yacht Charter,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Sochi,CA_CIS_006
discretion@confidentialtravel.ru,Maria Kozlova,Confidential Travel Russia,+7-495-789-0123,Russia,Discretion Lead,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Moscow,CA_CIS_007
estates@privatevillas.ru,Andrey Morozov,Private Villas CIS,+7-495-890-1234,Russia,Estate Curator,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Moscow,CA_CIS_008
wellness@biohacking.ru,Natalia Smirnova,Biohacking Travel Russia,+7-495-901-2345,Russia,Wellness Curator,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Moscow,CA_CIS_009
crypto@web3travel.ru,Alexey Petrov,Web3 Luxury Travel,+7-495-012-3456,Russia,Crypto Concierge,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Moscow,CA_CIS_010
corporate@boardretreats.ru,Irina Fedorova,Board Retreats CIS,+7-495-123-4568,Russia,Corporate Strategy,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Moscow,CA_CIS_011
passion@extremeluxury.ru,Viktor Orlov,Extreme Luxury Expeditions,+7-495-234-5679,Russia,Adventure Curator,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Kazan,CA_CIS_012
luxury@artindia.in,Kavita Desai,Art Collection India,+91-9822345678,India,Art Travel Specialist,LUXURY_CONCIERGE,A,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,West_India,CA_AO_013
luxury@artcollection.ru,Svetlana Novikova,Art Collection Travel,+7-495-345-6780,Russia,Art Travel Specialist,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,St. Petersburg,CA_CIS_013
private@familyoffice.ru,Mikhail Volkov,Family Office Travel,+7-495-456-7891,Russia,Family Office Liaison,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Moscow,CA_CIS_014
discretion@royaltravel.ru,Elena Popova,Royal Travel CIS,+7-495-567-8902,Russia,Royal Liaison,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Moscow,CA_CIS_015
luxury@techelite.ru,Anton Sokolov,Tech Elite Travel,+7-495-678-9013,Russia,Tech Concierge,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Moscow,CA_CIS_016
wellness@longevity.ru,Yulia Ivanova,Longevity Travel Russia,+7-495-789-0124,Russia,Longevity Specialist,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Sochi,CA_CIS_017
private@ultrahighnetworth.ru,Pavel Morozov,UHNW Travel Design,+7-495-890-1235,Russia,UHNW Specialist,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Moscow,CA_CIS_018
luxury@cryptowhale.ru,Maxim Petrov,Crypto Whale Travel,+7-495-901-2346,Russia,Crypto Luxury,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Moscow,CA_CIS_019
concierge@prestigecis.ru,Anna Kozlova,Prestige CIS Travel,+7-495-012-3457,Russia,Concierge Lead,LUXURY_CONCIERGE,A,prestige_cis_luxury,russia_luxury,unverified,TRUE,PENDING,Moscow,CA_CIS_020
luxury@nomadluxury.kz,Aigerim Nazarbayeva,Nomad Luxury Travel (Almaty),+7-727-234-5678,Kazakhstan,Director,LUXURY_CONCIERGE,A,prestige_cis_luxury,kazakhstan_luxury,unverified,TRUE,PENDING,Almaty,CA_CIS_021
private@steppeelite.kz,Bolat Temirbayev,Steppe Elite Travel,+7-727-345-6789,Kazakhstan,Founder,LUXURY_CONCIERGE,A,prestige_cis_luxury,kazakhstan_luxury,unverified,TRUE,PENDING,Nur-Sultan,CA_CIS_022
vip@astanaluxury.kz,Dinara Khamitova,Astana Luxury Concierge,+7-7172-456-789,Kazakhstan,VIP Manager,LUXURY_CONCIERGE,A,prestige_cis_luxury,kazakhstan_luxury,unverified,TRUE,PENDING,Nur-Sultan,CA_CIS_023
concierge@silkrouteluxury.kz,Ruslan Omarov,Silk Route Luxury Travel,+7-727-567-8901,Kazakhstan,Concierge Director,LUXURY_CONCIERGE,A,prestige_cis_luxury,kazakhstan_luxury,unverified,TRUE,PENDING,Almaty,CA_CIS_024
privatejet@skykaz.kz,Madina Suleimenova,Sky Kazakhstan Premium,+7-727-678-9012,Kazakhstan,Private Aviation,LUXURY_CONCIERGE,A,prestige_cis_luxury,kazakhstan_luxury,unverified,TRUE,PENDING,Almaty,CA_CIS_025
estates@caspiantours.kz,Arman Bekbayev,Caspian Luxury Estates,+7-727-789-0123,Kazakhstan,Estate Curator,LUXURY_CONCIERGE,A,prestige_cis_luxury,kazakhstan_luxury,unverified,TRUE,PENDING,Aktau,CA_CIS_026
wellness@biohackingkz.kz,Zarina Toleubaeva,Biohacking Travel KZ,+7-727-890-1234,Kazakhstan,Wellness Curator,LUXURY_CONCIERGE,A,prestige_cis_luxury,kazakhstan_luxury,unverified,TRUE,PENDING,Almaty,CA_CIS_027
corporate@boardkaz.kz,Nurlan Iskakov,Board Retreats Kazakhstan,+7-7172-901-234,Kazakhstan,Corporate Strategy,LUXURY_CONCIERGE,A,prestige_cis_luxury,kazakhstan_luxury,unverified,TRUE,PENDING,Nur-Sultan,CA_CIS_028
passion@extremekz.kz,Gulnara Abdrakhmanova,Extreme Luxury KZ,+7-727-012-3456,Kazakhstan,Adventure Curator,LUXURY_CONCIERGE,A,prestige_cis_luxury,kazakhstan_luxury,unverified,TRUE,PENDING,Almaty,CA_CIS_029
luxury@techkaz.kz,Timur Zhaksylykov,Tech Elite Kazakhstan,+7-727-123-4567,Kazakhstan,Tech Concierge,LUXURY_CONCIERGE,A,prestige_cis_luxury,kazakhstan_luxury,unverified,TRUE,PENDING,Almaty,CA_CIS_030
luxury@silkrouteluxury.uz,Dilnoza Karimova,Silk Route Luxury (Tashkent),+998-71-234-5678,Uzbekistan,Director,LUXURY_CONCIERGE,A,prestige_cis_luxury,uzbekistan_luxury,unverified,TRUE,PENDING,Tashkent,CA23605
private@samarkandelite.uz,Rustam Abdullaev,Samarkand Elite Travel,+998-71-345-6789,Uzbekistan,Founder,LUXURY_CONCIERGE,A,prestige_cis_luxury,uzbekistan_luxury,unverified,TRUE,PENDING,Samarkand,CA_CIS_031
vip@bukharaluxury.uz,Feruza Yusupova,Bukhara Luxury Concierge,+998-71-456-7890,Uzbekistan,VIP Manager,LUXURY_CONCIERGE,A,prestige_cis_luxury,uzbekistan_luxury,unverified,TRUE,PENDING,Bukhara,CA_CIS_032
concierge@khivaluxury.uz,Javlon Mirzayev,Khiva Luxury Travel,+998-71-567-8901,Uzbekistan,Concierge Director,LUXURY_CONCIERGE,A,prestige_cis_luxury,uzbekistan_luxury,unverified,TRUE,PENDING,Khiva,CA_CIS_033
estates@ferganaluxury.uz,Nargiza Rakhimova,Fergana Luxury Estates,+998-71-678-9012,Uzbekistan,Estate Curator,LUXURY_CONCIERGE,A,prestige_cis_luxury,uzbekistan_luxury,unverified,TRUE,PENDING,Fergana,CA_CIS_034
wellness@biohackinguz.uz,Azizbek Tursunov,Biohacking Travel Uzbekistan,+998-71-789-0123,Uzbekistan,Wellness Curator,LUXURY_CONCIERGE,A,prestige_cis_luxury,uzbekistan_luxury,unverified,TRUE,PENDING,Tashkent,CA_CIS_035
corporate@boarduz.uz,Shakhzod Ismailov,Board Retreats Uzbekistan,+998-71-890-1234,Uzbekistan,Corporate Strategy,LUXURY_CONCIERGE,A,prestige_cis_luxury,uzbekistan_luxury,unverified,TRUE,PENDING,Tashkent,CA_CIS_036
passion@extremeuz.uz,Malika Karimova,Extreme Luxury Uzbekistan,+998-71-901-2345,Uzbekistan,Adventure Curator,LUXURY_CONCIERGE,A,prestige_cis_luxury,uzbekistan_luxury,unverified,TRUE,PENDING,Tashkent,CA_CIS_037
luxury@armenialuxury.am,Ani Harutyunyan,Armenia Luxury Travel (Yerevan),+374-10-234-567,Armenia,Director,LUXURY_CONCIERGE,A,prestige_cis_luxury,armenia_luxury,unverified,TRUE,PENDING,Yerevan,CA13180
private@yerevanelite.am,Gor Sargsyan,Yerevan Elite Concierge,+374-10-345-678,Armenia,Founder,LUXURY_CONCIERGE,A,prestige_cis_luxury,armenia_luxury,unverified,TRUE,PENDING,Yerevan,CA_CIS_038
vip@sevanluxury.am,Lilit Grigoryan,Sevan Luxury Travel,+374-10-456-789,Armenia,VIP Manager,LUXURY_CONCIERGE,A,prestige_cis_luxury,armenia_luxury,unverified,TRUE,PENDING,Sevan,CA_CIS_039
concierge@dilijanluxury.am,Tigran Petrosyan,Dilijan Luxury Retreats,+374-10-567-890,Armenia,Concierge Director,LUXURY_CONCIERGE,A,prestige_cis_luxury,armenia_luxury,unverified,TRUE,PENDING,Dilijan,CA_CIS_040
wellness@biohackingam.am,Narine Mkrtchyan,Biohacking Travel Armenia,+374-10-678-901,Armenia,Wellness Curator,LUXURY_CONCIERGE,A,prestige_cis_luxury,armenia_luxury,unverified,TRUE,PENDING,Yerevan,CA_CIS_041
passion@extremearm.am,Armen Hakobyan,Extreme Luxury Armenia,+374-10-789-012,Armenia,Adventure Curator,LUXURY_CONCIERGE,A,prestige_cis_luxury,armenia_luxury,unverified,TRUE,PENDING,Yerevan,CA_CIS_042
luxury@bakuluxury.az,Leyla Aliyeva,Baku Luxury Travel (Baku),+994-12-234-5678,Azerbaijan,Director,LUXURY_CONCIERGE,A,prestige_cis_luxury,azerbaijan_luxury,unverified,TRUE,PENDING,Baku,CA_CIS_043
private@caspianelite.az,Rashad Mammadov,Caspian Elite Concierge,+994-12-345-6789,Azerbaijan,Founder,LUXURY_CONCIERGE,A,prestige_cis_luxury,azerbaijan_luxury,unverified,TRUE,PENDING,Baku,CA_CIS_044
vip@gabalaLuxury.az,Aysel Huseynova,Gabala Luxury Retreats,+994-12-456-7890,Azerbaijan,VIP Manager,LUXURY_CONCIERGE,A,prestige_cis_luxury,azerbaijan_luxury,unverified,TRUE,PENDING,Gabala,CA_CIS_045
concierge@shekiluxury.az,Elvin Aliyev,Sheki Luxury Travel,+994-12-567-8901,Azerbaijan,Concierge Director,LUXURY_CONCIERGE,A,prestige_cis_luxury,azerbaijan_luxury,unverified,TRUE,PENDING,Sheki,CA_CIS_046
wellness@biohackingaz.az,Nigar Ismayilova,Biohacking Travel Azerbaijan,+994-12-678-9012,Azerbaijan,Wellness Curator,LUXURY_CONCIERGE,A,prestige_cis_luxury,azerbaijan_luxury,unverified,TRUE,PENDING,Baku,CA_CIS_047
corporate@boardaz.az,Farid Mammadov,Board Retreats Azerbaijan,+994-12-789-0123,Azerbaijan,Corporate Strategy,LUXURY_CONCIERGE,A,prestige_cis_luxury,azerbaijan_luxury,unverified,TRUE,PENDING,Baku,CA_CIS_048
"""

lines = raw_data.strip().split('\n')
writer = csv.writer(sys.stdout)

for line in lines:
    row = line.split(',')
    if len(row) < 10: continue

    email = row[0]
    contact_name = row[1]
    company = row[2]
    phone = row[3]
    country = row[4]
    role = row[5]
    agent_type = row[6]
    priority = row[7]
    segment = row[8]
    # Internal format: email,company,region,country,agent_type,priority_tier,contact_role,status,trigger_segment,last_contact,notes
    writer.writerow([
        email, company, "CIS", country, agent_type, priority, role, "unverified", segment, "", f"{contact_name} | {phone}"
    ])
