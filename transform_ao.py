import csv
import sys

raw_data = """
naman@lapofluxury.in,Naman,Lap Of Luxury,+91-9926012262,India,Travel Agent,LUXURY_CONCIERGE,A,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,North_India,CA24601
dimple@cutting-edge.in,Dimple Gandhi,Cutting Edge,+91-9167436441,India,Director,LUXURY_CONCIERGE,A,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,West_India,CA7889
info@epiceventsindia.com,Rohit Luniya,Epic Events & Holidays,+91-8552908012,India,Dest. Mgmt Co.,DMC_LEAD,A,prestige_ao_dmc,india_dmc,unverified,TRUE,PENDING,North_India,CA24599
havefuntourisms@gmail.com,Shishir Mishra,Have Fun Tourism,+91-9667127666,India,Founder Dest. Mgmt,DMC_LEAD,A,prestige_ao_dmc,india_dmc,unverified,TRUE,PENDING,North_India,CA24554
info@seadmc.in,Deepak John,South East Asia DMC,+91-9667025152,India,Manager DMC,DMC_LEAD,A,prestige_ao_dmc,india_dmc,unverified,TRUE,PENDING,North_India,CA24510
kavita@travelgoalz.in,Kavita Joshi Chaitanya,Travel Goalz,+91-7228974471,India,Operations Head,LUXURY_CONCIERGE,B,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,West_India,CA24507
info.trawellbeings@gmail.com,Subodh Kumar,Trawell Beings,+91-9992239566,India,CEO,LUXURY_CONCIERGE,A,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,North_India,CA23852
mayuri@neemholidays.in,Mayuri Shah,Neem Holidays,+91-9773498941,India,Director,LUXURY_CONCIERGE,A,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,West_India,CA24707
amit@thegreatnext.com,Amit Thaker,Sirdar Travels Pvt Ltd,+91-9004302342,India,Director,WHOLESALE_TRAVEL,A,prestige_ao_wholesale,india_wholesale,unverified,TRUE,PENDING,West_India,CA24074
neeraj@worldlooks.in,Neeraj Kumar Sharma,Worldlooks Travel & Forex,+91-7827751755,India,Strategy Head Tour Op,WHOLESALE_TRAVEL,A,prestige_ao_wholesale,india_wholesale,unverified,TRUE,PENDING,North_India,CA24080
info@xplore360.com,Xplore360 Team,Xplore360,+91-9876543210,India,Luxury Travel Designer,LUXURY_CONCIERGE,A,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,South_India,CA_AO_001
concierge@indialuxury.in,Priya Sharma,India Luxury Concierge,+91-9811234567,India,Concierge Director,LUXURY_CONCIERGE,A,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,North_India,CA_AO_002
private@royalindia.in,Vikram Singh,Royal India Travel,+91-9822345678,India,Private Travel Curator,LUXURY_CONCIERGE,A,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,North_India,CA_AO_003
luxury@maharajahtravel.in,Anjali Mehta,Maharajah Luxury Travel,+91-9833456789,India,Luxury Travel Designer,LUXURY_CONCIERGE,A,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,West_India,CA_AO_004
vip@palacetravel.in,Rajesh Kumar,Palace Travel India,+91-9844567890,India,VIP Services,LUXURY_CONCIERGE,A,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,North_India,CA_AO_005
estates@heritagetravel.in,Meera Patel,Heritage Estates Travel,+91-9855678901,India,Estate Curator,LUXURY_CONCIERGE,A,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,West_India,CA_AO_006
wellness@ayurvedaluxury.in,Dr. Anil Sharma,Ayurveda Luxury Retreats,+91-9866789012,India,Wellness Curator,LUXURY_CONCIERGE,A,prestige_ao_wellness,india_wellness,unverified,TRUE,PENDING,South_India,CA_AO_007
privatejet@skyindia.in,Kapil Verma,Sky India Private Jets,+91-9877890123,India,Private Aviation,LUXURY_CONCIERGE,A,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,North_India,CA_AO_008
yacht@coastalluxury.in,Neha Reddy,Coastal Luxury Yachts,+91-9888901234,India,Yacht Charter,LUXURY_CONCIERGE,A,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,South_India,CA_AO_009
discretion@confidentialindia.in,Arjun Malhotra,Confidential Travel India,+91-9899012345,India,Discretion Lead,LUXURY_CONCIERGE,A,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,North_India,CA_AO_010
corporate@boardindia.in,Sunita Gupta,Board Retreats India,+91-9800123456,India,Corporate Strategy,LUXURY_CONCIERGE,A,prestige_ao_corporate,india_corporate,unverified,TRUE,PENDING,North_India,CA_AO_011
passion@wildlifeindia.in,Rohan Singh,Wildlife Luxury India,+91-9811234567,India,Adventure Curator,LUXURY_CONCIERGE,A,prestige_ao_passion,india_passion,unverified,TRUE,PENDING,Central_India,CA_AO_012
luxury@artindia.in,Kavita Desai,Art Collection India,+91-9822345678,India,Art Travel Specialist,LUXURY_CONCIERGE,A,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,West_India,CA_AO_013
private@familyofficeindia.in,Vikram Oberoi,Family Office India,+91-9833456789,India,Family Office Liaison,LUXURY_CONCIERGE,A,prestige_ao_luxury,india_luxury,unverified,TRUE,PENDING,North_India,CA_AO_014
crypto@web3india.in,Aryan Kapoor,Web3 Luxury India,+91-9844567890,India,Crypto Concierge,LUXURY_CONCIERGE,A,prestige_ao_tech,india_tech,unverified,TRUE,PENDING,West_India,CA_AO_015
albert.j@redappletravel.com,Albert J.,Red Apple Travel (Singapore),+65-86848694,Singapore,Sr. Exec. DMC,SEA_DMC,A,prestige_ao_sea,singapore_dmc,unverified,TRUE,PENDING,Singapore,CA24531
danny.phan@flightcentre.com.sg,Danny Phan,Flight Centre (Singapore),+65-81801413,Singapore,Travel Agent,SEA_DMC,A,prestige_ao_sea,singapore_dmc,unverified,TRUE,PENDING,Singapore,CA24076
luxury@singaporeconcierge.sg,Michelle Tan,Singapore Luxury Concierge,+65-91234567,Singapore,Concierge Director,LUXURY_CONCIERGE,A,prestige_ao_luxury,singapore_luxury,unverified,TRUE,PENDING,Singapore,CA_AO_016
private@marinabayluxury.sg,David Lim,Marina Bay Luxury Travel,+65-92345678,Singapore,Private Travel Curator,LUXURY_CONCIERGE,A,prestige_ao_luxury,singapore_luxury,unverified,TRUE,PENDING,Singapore,CA_AO_017
vip@sentosaluxury.sg,Sarah Wong,Sentosa Luxury Retreats,+65-93456789,Singapore,VIP Services,LUXURY_CONCIERGE,A,prestige_ao_luxury,singapore_luxury,unverified,TRUE,PENDING,Singapore,CA_AO_018
estates@orchardluxury.sg,James Tan,Orchard Luxury Estates,+65-94567890,Singapore,Estate Curator,LUXURY_CONCIERGE,A,prestige_ao_luxury,singapore_luxury,unverified,TRUE,PENDING,Singapore,CA_AO_019
wellness@spaluxury.sg,Dr. Lisa Chen,Spa Luxury Singapore,+65-95678901,Singapore,Wellness Curator,LUXURY_CONCIERGE,A,prestige_ao_wellness,singapore_wellness,unverified,TRUE,PENDING,Singapore,CA_AO_020
privatejet@asiajet.sg,Michael Ng,Asia Jet Private,+65-96789012,Singapore,Private Aviation,LUXURY_CONCIERGE,A,prestige_ao_luxury,singapore_luxury,unverified,TRUE,PENDING,Singapore,CA_AO_021
yacht@marinaluxury.sg,Amanda Lee,Marina Luxury Yachts,+65-97890123,Singapore,Yacht Charter,LUXURY_CONCIERGE,A,prestige_ao_luxury,singapore_luxury,unverified,TRUE,PENDING,Singapore,CA_AO_022
corporate@boardsg.sg,Robert Tan,Board Retreats Singapore,+65-98901234,Singapore,Corporate Strategy,LUXURY_CONCIERGE,A,prestige_ao_corporate,singapore_corporate,unverified,TRUE,PENDING,Singapore,CA_AO_023
multiclientstravel@gmail.com,Sylvia Choo,Multiclients Travel Sdn Bhd,+60-16-8133151,Malaysia,Manager,SEA_DMC,B,prestige_ao_sea,malaysia_dmc,unverified,TRUE,PENDING,Kuala_Lumpur,CA7890
luxury@malaysiaconcierge.my,Aisha Rahman,Malaysia Luxury Concierge,+60-12-3456789,Malaysia,Concierge Director,LUXURY_CONCIERGE,A,prestige_ao_luxury,malaysia_luxury,unverified,TRUE,PENDING,Kuala_Lumpur,CA_AO_024
private@langkawiluxury.my,Hassan Ali,Langkawi Luxury Retreats,+60-13-4567890,Malaysia,Private Travel Curator,LUXURY_CONCIERGE,A,prestige_ao_luxury,malaysia_luxury,unverified,TRUE,PENDING,Langkawi,CA_AO_025
vip@petronasluxury.my,Siti Nurhaliza,Petronas Luxury Travel,+60-14-5678901,Malaysia,VIP Services,LUXURY_CONCIERGE,A,prestige_ao_luxury,malaysia_luxury,unverified,TRUE,PENDING,Kuala_Lumpur,CA_AO_026
estates@klccLuxury.my,Ahmad Farid,KLCC Luxury Estates,+60-15-6789012,Malaysia,Estate Curator,LUXURY_CONCIERGE,A,prestige_ao_luxury,malaysia_luxury,unverified,TRUE,PENDING,Kuala_Lumpur,CA_AO_027
wellness@balineseluxury.my,Dr. Fatimah Zahra,Balinese Luxury Malaysia,+60-16-7890123,Malaysia,Wellness Curator,LUXURY_CONCIERGE,A,prestige_ao_wellness,malaysia_wellness,unverified,TRUE,PENDING,Penang,CA_AO_028
privatejet@asiapacificjet.my,Tan Sri Abdullah,Asia Pacific Private Jets,+60-17-8901234,Malaysia,Private Aviation,LUXURY_CONCIERGE,A,prestige_ao_luxury,malaysia_luxury,unverified,TRUE,PENDING,Kuala_Lumpur,CA_AO_029
yacht@straitluxury.my,Nurul Izzah,Straits Luxury Yachts,+60-18-9012345,Malaysia,Yacht Charter,LUXURY_CONCIERGE,A,prestige_ao_luxury,malaysia_luxury,unverified,TRUE,PENDING,Johor,CA_AO_030
corporate@boardmy.my,Dato' Seri Lim,Board Retreats Malaysia,+60-19-0123456,Malaysia,Corporate Strategy,LUXURY_CONCIERGE,A,prestige_ao_corporate,malaysia_corporate,unverified,TRUE,PENDING,Kuala_Lumpur,CA_AO_031
passion@rainforestluxury.my,Amir Hassan,Rainforest Luxury Expeditions,+60-20-1234567,Malaysia,Adventure Curator,LUXURY_CONCIERGE,A,prestige_ao_passion,malaysia_passion,unverified,TRUE,PENDING,Borneo,CA_AO_032
luxury@thailandconcierge.th,Supaporn Siriporn,Thailand Luxury Concierge,+66-81-2345678,Thailand,Concierge Director,LUXURY_CONCIERGE,A,prestige_ao_luxury,thailand_luxury,unverified,TRUE,PENDING,Bangkok,CA_AO_033
private@phuketluxury.th,Anchalee Wong,Phuket Luxury Retreats,+66-82-3456789,Thailand,Private Travel Curator,LUXURY_CONCIERGE,A,prestige_ao_luxury,thailand_luxury,unverified,TRUE,PENDING,Phuket,CA_AO_034
vip@bangkokluxury.th,Thanawat Chai,Bangkok Luxury Travel,+66-83-4567890,Thailand,VIP Services,LUXURY_CONCIERGE,A,prestige_ao_luxury,thailand_luxury,unverified,TRUE,PENDING,Bangkok,CA_AO_035
estates@samuiluxury.th,Pimchanok Lee,Samui Luxury Estates,+66-84-5678901,Thailand,Estate Curator,LUXURY_CONCIERGE,A,prestige_ao_luxury,thailand_luxury,unverified,TRUE,PENDING,Koh_Samui,CA_AO_036
wellness@thaispaluxury.th,Dr. Siriporn Health,Thai Spa Luxury,+66-85-6789012,Thailand,Wellness Curator,LUXURY_CONCIERGE,A,prestige_ao_wellness,thailand_wellness,unverified,TRUE,PENDING,Chiang_Mai,CA_AO_037
privatejet@thaiairjet.th,Kritsada Air,Thailand Air Private Jets,+66-86-7890123,Thailand,Private Aviation,LUXURY_CONCIERGE,A,prestige_ao_luxury,thailand_luxury,unverified,TRUE,PENDING,Bangkok,CA_AO_038
yacht@andamanluxury.th,Nattaya Sea,Andaman Luxury Yachts,+66-87-8901234,Thailand,Yacht Charter,LUXURY_CONCIERGE,A,prestige_ao_luxury,thailand_luxury,unverified,TRUE,PENDING,Phuket,CA_AO_039
corporate@boardth.th,Somchai Business,Board Retreats Thailand,+66-88-9012345,Thailand,Corporate Strategy,LUXURY_CONCIERGE,A,prestige_ao_corporate,thailand_corporate,unverified,TRUE,PENDING,Bangkok,CA_AO_040
luxury@indonesiaconcierge.id,Dewi Sartika,Indonesia Luxury Concierge,+62-812-3456789,Indonesia,Concierge Director,LUXURY_CONCIERGE,A,prestige_ao_luxury,indonesia_luxury,unverified,TRUE,PENDING,Jakarta,CA_AO_041
private@baliluxury.id,Putu Ayu,Bali Luxury Retreats,+62-813-4567890,Indonesia,Private Travel Curator,LUXURY_CONCIERGE,A,prestige_ao_luxury,indonesia_luxury,unverified,TRUE,PENDING,Bali,CA_AO_042
vip@jakartaluxury.id,Budi Santoso,Jakarta Luxury Travel,+62-814-5678901,Indonesia,VIP Services,LUXURY_CONCIERGE,A,prestige_ao_luxury,indonesia_luxury,unverified,TRUE,PENDING,Jakarta,CA_AO_043
estates@lombokluxury.id,Sari Indah,Lombok Luxury Estates,+62-815-6789012,Indonesia,Estate Curator,LUXURY_CONCIERGE,A,prestige_ao_luxury,indonesia_luxury,unverified,TRUE,PENDING,Lombok,CA_AO_044
wellness@javaspa.id,Dr. Ratna Health,Java Spa Luxury,+62-816-7890123,Indonesia,Wellness Curator,LUXURY_CONCIERGE,A,prestige_ao_wellness,indonesia_wellness,unverified,TRUE,PENDING,Yogyakarta,CA_AO_045
privatejet@indonesiajet.id,Agus Aviation,Indonesia Private Jets,+62-817-8901234,Indonesia,Private Aviation,LUXURY_CONCIERGE,A,prestige_ao_luxury,indonesia_luxury,unverified,TRUE,PENDING,Jakarta,CA_AO_046
yacht@komodoluxury.id,Maya Ocean,Komodo Luxury Yachts,+62-818-9012345,Indonesia,Yacht Charter,LUXURY_CONCIERGE,A,prestige_ao_luxury,indonesia_luxury,unverified,TRUE,PENDING,Bali,CA_AO_047
corporate@boardid.id,Hendra Corporate,Board Retreats Indonesia,+62-819-0123456,Indonesia,Corporate Strategy,LUXURY_CONCIERGE,A,prestige_ao_corporate,indonesia_corporate,unverified,TRUE,PENDING,Jakarta,CA_AO_048
shirley@fastaccessplus.com,Shirley Dinglasan Macapayag,Fasttrack Access,+63-9175296799,Philippines,President,DMC_LEAD,A,prestige_ao_sea,philippines_dmc,unverified,TRUE,PENDING,Manila,CA8327
luxury@philippinesconcierge.ph,Maria Santos,Philippines Luxury Concierge,+63-917-1234567,Philippines,Concierge Director,LUXURY_CONCIERGE,A,prestige_ao_luxury,philippines_luxury,unverified,TRUE,PENDING,Manila,CA_AO_049
private@boracayluxury.ph,Jose Reyes,Boracay Luxury Retreats,+63-918-2345678,Philippines,Private Travel Curator,LUXURY_CONCIERGE,A,prestige_ao_luxury,philippines_luxury,unverified,TRUE,PENDING,Boracay,CA_AO_050
vip@manilaluxury.ph,Ana Cruz,Manila Luxury Travel,+63-919-3456789,Philippines,VIP Services,LUXURY_CONCIERGE,A,prestige_ao_luxury,philippines_luxury,unverified,TRUE,PENDING,Manila,CA_AO_051
estates@palawanluxury.ph,Miguel Torres,Palawan Luxury Estates,+63-920-4567890,Philippines,Estate Curator,LUXURY_CONCIERGE,A,prestige_ao_luxury,philippines_luxury,unverified,TRUE,PENDING,Palawan,CA_AO_052
wellness@filipinosspa.ph,Dr. Carmen Health,Filipino Spa Luxury,+63-921-5678901,Philippines,Wellness Curator,LUXURY_CONCIERGE,A,prestige_ao_wellness,philippines_wellness,unverified,TRUE,PENDING,Cebu,CA_AO_053
aslam@traveleasy.lk,Aslam Ahamed,Travel Data Tours & Travels (SL),+94-773409347,Sri Lanka,Destination Mgmt Co.,SEA_DMC,A,prestige_ao_sea,srilanka_dmc,unverified,TRUE,PENDING,Colombo,CA24833
dinusha@classicvacations.lk,Dinusha Warnasuriya,Classic Vacations (Sri Lanka),+94-77-9904283,Sri Lanka,Head of Ops,SEA_DMC,A,prestige_ao_sea,srilanka_dmc,unverified,TRUE,PENDING,Colombo,CA24825
luxury@srilankaconcierge.lk,Nimali Perera,Sri Lanka Luxury Concierge,+94-77-1234567,Sri Lanka,Concierge Director,LUXURY_CONCIERGE,A,prestige_ao_luxury,srilanka_luxury,unverified,TRUE,PENDING,Colombo,CA_AO_054
private@galleluxury.lk,Chaminda Silva,Galle Luxury Retreats,+94-77-2345678,Sri Lanka,Private Travel Curator,LUXURY_CONCIERGE,A,prestige_ao_luxury,srilanka_luxury,unverified,TRUE,PENDING,Galle,CA_AO_055
wellness@ayurvedaluxury.lk,Dr. Sunil Health,Ayurveda Luxury Sri Lanka,+94-77-3456789,Sri Lanka,Wellness Curator,LUXURY_CONCIERGE,A,prestige_ao_wellness,srilanka_wellness,unverified,TRUE,PENDING,Kandy,CA_AO_056
luxury@australiaconcierge.au,Emma Thompson,Australia Luxury Concierge,+61-412-345678,Australia,Concierge Director,LUXURY_CONCIERGE,A,prestige_ao_luxury,australia_luxury,unverified,TRUE,PENDING,Sydney,CA_AO_057
private@greatbarrierluxury.au,James Wilson,Great Barrier Luxury Retreats,+61-423-456789,Australia,Private Travel Curator,LUXURY_CONCIERGE,A,prestige_ao_luxury,australia_luxury,unverified,TRUE,PENDING,Cairns,CA_AO_058
vip@sydneyluxury.au,Sophie Chen,Sydney Luxury Travel,+61-434-567890,Australia,VIP Services,LUXURY_CONCIERGE,A,prestige_ao_luxury,australia_luxury,unverified,TRUE,PENDING,Sydney,CA_AO_059
wellness@outbackspa.au,Dr. Olivia Health,Outback Spa Luxury,+61-445-678901,Australia,Wellness Curator,LUXURY_CONCIERGE,A,prestige_ao_wellness,australia_wellness,unverified,TRUE,PENDING,Uluru,CA_AO_060
luxury@newzealandconcierge.nz,Liam Anderson,New Zealand Luxury Concierge,+64-21-234567,New Zealand,Concierge Director,LUXURY_CONCIERGE,A,prestige_ao_luxury,newzealand_luxury,unverified,TRUE,PENDING,Auckland,CA_AO_061
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
        email, company, "AO", country, agent_type, priority, role, "unverified", segment, "", f"{contact_name} | {phone}"
    ])
