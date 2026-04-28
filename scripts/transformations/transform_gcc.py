import csv
import sys

raw_data = """
tamer.m@redappletravel.com,Tamer Magdy,Red Apple Travel (GCC Luxury),+971-503481772,UAE,General Manager Sales - GCC,LUXURY_CONCIERGE,A,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA24831
kiran.shetty@lotsofhotels.com,Kiran Shetty,Lots Of Hotels (Luxury Division),+971-564992933,UAE,Director Of Sales,LUXURY_WHOLESALE,A,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA13548
a.pytlik@panworldtravels.com,Aga Pytlik,Panworld Travel & Tourism (Premium),+971-504160418,UAE,Deputy General Manager,LUXURY_CONCIERGE,A,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA22971
gopal@travrays.com,Gopalakrishnan V,TravRays Travels LLC (Luxury),+971-564548511,UAE,Manager,LUXURY_CONCIERGE,B,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA21360
bouchra.ider@jossour-privileges.com,Bouchra Ider,JOSSOUR EVENTS MANAGEMENT (VIP),+971-526748116,UAE,GENERAL MANAGER,LUXURY_CONCIERGE,A,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA21338
jeet@laurustravelsolutions.com,Jitender Kumar,Laurus Travel Solutions (Premium),+971-528294974,UAE,Director - Business,LUXURY_CONCIERGE,A,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA22359
naman@lapofluxury.in,Naman,Lap Of Luxury (GCC Desk),+91-9926012262,UAE,Travel Agent,LUXURY_CONCIERGE,A,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA24601
lokith@justdialholidays.com,Lokith Keswani,Just Dial Holidays LLC (Luxury),+971-589078057,UAE,MD,LUXURY_CONCIERGE,A,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA24401
rahul@btwgroup.co,Rahul,BTW Group (Luxury Division),+91-8308380200,UAE,Director Sales,LUXURY_CONCIERGE,A,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA16825
toby@colorsholidays.com,Toby Thomas,Colors Holidays LLC (Premium),+971-501162907,UAE,Director of Operations,LUXURY_CONCIERGE,A,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA23546
mail@halaldays.com,Nahiyan Najeeb,HALALDAYS (Luxury Halal Travel),+971-556974949,UAE,MANAGER,LUXURY_CONCIERGE,A,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Sharjah,CA24784
info@luxetm.in,Tarun Bansal,Luxe Travel Management,+91-7823047585,UAE,Manager operations,LUXURY_CONCIERGE,B,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA16169
jp@tripmayntra.com,Jaiprakash Doliya,TripMayntra Travel (Luxury DMC),+971-564041676,UAE,General Manager,LUXURY_DMC,A,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Fujairah,CA16168
annabelle@guardiantourism.com,Annabelle Canega,Guardian Tourism (Premium),+971-504368931,UAE,Travel Associate,LUXURY_CONCIERGE,B,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA9998
zaid@afttc.ae,Zaid Nazir,AlFajer Travel & Tourism (Luxury),+971-502849447,UAE,Travel Consultant,LUXURY_CONCIERGE,B,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA9999
jasmine@trvex.com,Jasmine Kaur,Travex Tourism (Premium),+971-551082564,UAE,Sales & Marketing Manager,LUXURY_CONCIERGE,B,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA9807
moayad@arabianstar.de,Moayad Eid,ARABIAN STAR TOURS LLC (Luxury),+971-558869988,UAE,manager,LUXURY_CONCIERGE,A,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA14891
tamer.magdy@skylinetravel.ae,Tamer Magdy,Skyline Travel & Tourism (Premium),+971-564758145,UAE,Director Of,LUXURY_CONCIERGE,A,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Abu Dhabi,CA16800
daly@prolinktravel.com,Mohamedali Ben Yedder,PROLINK TRAVEL (Luxury),+971-554723070,UAE,LUXURY_CONCIERGE,A,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA11905
mahesh@horizontours.ae,Mahesh Mirchandani,HORIZON TOURS LLC (Premium DMC),+971-505879361,UAE,MANAGING DIRECTOR,LUXURY_DMC,A,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA11104
nidhin@akbargulf.com,Nidhin MK,AKBAR TRAVELS OF INDIA LLC (Luxury GCC),+971-506983484,UAE,TOUR CONSULTANT,LUXURY_WHOLESALE,A,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA10497
nejela@exoticuae.com,Nejela Johns,Exotic Tours & Travels DMCC (Luxury),+971-509978215,UAE,Travel Consultant,LUXURY_CONCIERGE,B,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA10036
amaro@masatours.com,Amaro Basco,Masa Tours (Premium),+971-555109437,UAE,Travel Consultant,LUXURY_CONCIERGE,B,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA10035
andrew@superjetgroup.com,Andrew Barra,Superjet Worldwide Tours (Luxury),+971-555109437,UAE,Reservation Manager,LUXURY_CONCIERGE,B,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA10243
lancy@uranustravel.com,Lancy Desouza,URANUS TRAVEL & TOURS (Premium),+971-522916658,UAE,Travel Agent,LUXURY_CONCIERGE,B,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Dubai,CA7262
gm.travel@worldtravellerco.com,Safeiudin Mohamed,World Traveler Company (Luxury KSA),+966-569695112,Saudi Arabia,General Manager,LUXURY_CONCIERGE,A,prestige_gcc_luxury,ksa_luxury,unverified,TRUE,PENDING,Riyadh,CA7582
hazem@globallines.com,Hazem Alomari,Global lines (Premium),+966-537556644,Saudi Arabia,Branch Manager,LUXURY_CONCIERGE,B,prestige_gcc_luxury,ksa_luxury,unverified,TRUE,PENDING,Buraidah,CA6077
holidays@nicetripholidays.net,Ashraf Fahmy,Nice Trip Holidays (Luxury FIT),+966-567533395,Saudi Arabia,Tourism Manager,LUXURY_CONCIERGE,B,prestige_gcc_luxury,ksa_luxury,unverified,TRUE,PENDING,Jeddah,CA5636
nisanthsk26@gmail.com,Nisanthan Santha Kumari,FURSAN HOLIDAYS (Luxury Wholesale),+966-542596324,Saudi Arabia,CHIEF EXECUTIVE OFFICER,LUXURY_WHOLESALE,A,prestige_gcc_luxury,ksa_luxury,unverified,TRUE,PENDING,Abha,CA12499
farishahid94@gmail.com,Farwa Shahid,AL MARWAH TRAVEL AND TOURISM (Premium),+966-557332087,Saudi Arabia,TRAVEL CONSULTANT,LUXURY_CONCIERGE,B,prestige_gcc_luxury,ksa_luxury,unverified,TRUE,PENDING,Ajman,CA19132
a-c-l@hotmail.com,Anis Ahmad Alhomsi,luxury travel (Premium KSA),+966-552223119,Saudi Arabia,Travel Agent,LUXURY_CONCIERGE,B,prestige_gcc_luxury,ksa_luxury,unverified,TRUE,PENDING,Buraydah,CA8023
yazan@luxurytours-jo.com,Yazan Yacoub Sunna,Luxury Travel & Tours (GCC Luxury),+962-795004020,Saudi Arabia,Director of Sales and Marketing,LUXURY_CONCIERGE,A,prestige_gcc_luxury,ksa_luxury,unverified,TRUE,PENDING,Amman,CA23450
info@mumtaztours.com,Sreejith Nambiar,Mumtaz Tours & Travels (Premium),+968-92963535,Oman,Business Development Manager,LUXURY_CONCIERGE,A,prestige_gcc_luxury,oman_luxury,unverified,TRUE,PENDING,Muscat,CA23890
ayaz@bestchoicetravel.net,Hussain Syed Ayaz,BEST CHOICE TRAVEL AND TOURS (Luxury),+968-95866351,Oman,Tour Operator,LUXURY_CONCIERGE,A,prestige_gcc_luxury,oman_luxury,unverified,TRUE,PENDING,Muscat,CA12630
almaamaritours@outlook.com,Munerah Al Azry,AL MAAMARI TOURS (Premium Oman),+968-97019931,Oman,Travel Agent,LUXURY_CONCIERGE,B,prestige_gcc_luxury,oman_luxury,unverified,TRUE,PENDING,Muscat,CA12151
khaled@travelwithalpha.com,Khaled Rustom,Alpha Omega Travel (Luxury Qatar),+974-55840073,Qatar,General Manager,LUXURY_CONCIERGE,A,prestige_gcc_luxury,qatar_luxury,unverified,TRUE,PENDING,Doha,CA24072
a.elsayed@link-travels.com,Ahmed El Sayed Mahmoud,Link Travel and Tourism (Premium),+974-50626054,Qatar,Operations and Sales Manager,LUXURY_CONCIERGE,B,prestige_gcc_luxury,qatar_luxury,unverified,TRUE,PENDING,Doha,CA8043
vinod@avensholidays.com,Vinod Kumar,Avens Holidays (Luxury Qatar),+974-55935992,Qatar,Travel Agent,LUXURY_CONCIERGE,B,prestige_gcc_luxury,qatar_luxury,unverified,TRUE,PENDING,Doha,CA11985
shahzad@check-inn.tv,Shahzad Alam,check inn (Premium Qatar),+974-33720962,Qatar,Travel Agent,LUXURY_CONCIERGE,B,prestige_gcc_luxury,qatar_luxury,unverified,TRUE,PENDING,Doha,CA11972
smarti20008@hotmail.com,Siddim Emmanuel,Global Tourist (Luxury Qatar),+974-30680836,Qatar,Travel Agent,LUXURY_CONCIERGE,B,prestige_gcc_luxury,qatar_luxury,unverified,TRUE,PENDING,Doha,CA11971
mano@falcontravelqatar.com,Mano,Falcon Travel (Premium),+974-44354777,Qatar,Travel Agent,LUXURY_CONCIERGE,B,prestige_gcc_luxury,qatar_luxury,unverified,TRUE,PENDING,Doha,CA11970
annaly@gttoman.com,Annalyn Esmilla,Giants Travel (Luxury Oman),+968-94901132,Oman,Travel Agent,LUXURY_CONCIERGE,B,prestige_gcc_luxury,oman_luxury,unverified,TRUE,PENDING,Muscat,CA12623
hyde@dhafirts.ae,Haydee Mercado,Dhafir Travel AUH (Premium),+971-26219319,UAE,Travel Consultant,LUXURY_CONCIERGE,B,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Abu Dhabi,CA10252
newraklt@eim.ae,Lincoln Edwin,NEWRAK LEISURE TRAVEL & TOURISM (Luxury),+971-504328848,UAE,Travel Manager,LUXURY_CONCIERGE,B,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Ras Al Khaimah,CA10244
rk@untauaq.ae,Radhakrishnan Gopalan,UMM AL QUWAIN NATIONAL TRAVEL (Premium),+971-508935758,UAE,Supervisor,LUXURY_CONCIERGE,B,prestige_gcc_luxury,uae_luxury,unverified,TRUE,PENDING,Umm Al Quwain,CA10374
bibin@eternityholidays.com,Bibin Suresh,Eternity Holidays (Luxury Kuwait),+965-65017888,Kuwait,Head- Holidays,LUXURY_CONCIERGE,A,prestige_gcc_luxury,kuwait_luxury,unverified,TRUE,PENDING,Kuwait City,CA8695
ciaocaro2010@hotmail.com,Ahmed Abdallah,Bravo Travel & Tourism (Premium),+965-99699150,Kuwait,Travel Agent,LUXURY_CONCIERGE,B,prestige_gcc_luxury,kuwait_luxury,unverified,TRUE,PENDING,Kuwait City,CA8231
marveltravel.kw@gmail.com,Mahmoud Shams,Marvel Travel (Luxury Kuwait),+965-66612759,Kuwait,CEO,LUXURY_CONCIERGE,A,prestige_gcc_luxury,kuwait_luxury,unverified,TRUE,PENDING,Kuwait City,CA23947
info@mumtaztours.com,Sreejith Nambiar,Mumtaz Tours & Travels (Premium Oman),+968-92963535,Oman,Business Development Manager,LUXURY_CONCIERGE,A,prestige_gcc_luxury,oman_luxury,unverified,TRUE,PENDING,Muscat,CA23890
ayaz@bestchoicetravel.net,Hussain Syed Ayaz,BEST CHOICE TRAVEL AND TOURS (Luxury),+968-95866351,Oman,Tour Operator,LUXURY_CONCIERGE,A,prestige_gcc_luxury,oman_luxury,unverified,TRUE,PENDING,Muscat,CA12630
almaamaritours@outlook.com,Munerah Al Azry,AL MAAMARI TOURS (Premium),+968-97019931,Oman,Travel Agent,LUXURY_CONCIERGE,B,prestige_gcc_luxury,oman_luxury,unverified,TRUE,PENDING,Muscat,CA12151
annaly@gttoman.com,Annalyn Esmilla,Giants Travel (Luxury Oman),+968-94901132,Oman,Travel Agent,LUXURY_CONCIERGE,B,prestige_gcc_luxury,oman_luxury,unverified,TRUE,PENDING,Muscat,CA12623
"""

lines = raw_data.strip().split('\n')
writer = csv.writer(sys.stdout)

for line in lines:
    row = line.split(',')
    if len(row) < 15: continue

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
        email, company, "GCC", country, agent_type, priority, role, "unverified", segment, "", f"{contact_name} | {phone}"
    ])
