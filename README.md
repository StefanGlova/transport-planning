# transport-planning

Transport planning application is created as part of supply chain apps pack by Stefan Glova. This application is designed for manufacturing businesses.
which distribute their own products. The reason for that specification is, that manufacturing businesses, especially if they produce 100s or 1000s of SKUs,
may receive order from their customer before product is made and may need to deliver part of order which is available and redeliver remining SKUs later. This 
in practice makes transport planning challenging.

Application is designed to take 5 arguments: 
1. volume target - this is in m3, what is minimum fill of delivery vehicle (trailer) to make it economical for delivery.
2. volume max - this is in m3, maximum capacity of delivery vehicle (trailer)
      each planned delivery is going to be between these two values.
3. minimum volume - this is in m3, and it is minimum size of individual delivery to make it economical for delivery, otherwise, the app will plan it as delivery
by 3rd party carrier / parcel service
4. order file - this is csv file which contains list of orders which are required for transport planning.
5. inventory file - this is csv file which contains list of all available SKUs and their available qty.

The application is based on Clarke-Wright Saving Algorithm with extra implementation for inventory allocation during planning process. Original algorithm 
expect 100 % availability.

Step 1 - Application first plan all deliveries, which are big enough to fill delivery vehicle on their own. 

Step 2 - Then it planes all left, if they meet minimum volume argument.

Step 3 - At the end it plans all what is left for carrier / parcel 3rd party service.

The most important and the most complex part is Step 2:
1. It first creates list of all postcodes pairs for all deliveries (100 delivery postcodes,
gives nearly 5000 postcodes pairs). 
2. Then it calculates distance between each postcode pair (if 100 postcodes, 5000 pairs = 5000 distance information), based on latitude and longitude
of each postcode. It uses the UK postcode database with approx. 1,700,000 postcodes to get latitude and longitude.
3. Origin destination is set up as part of the app, not as user's input argument. Next step is to calculate distance between origin and all destinations.
4. It calculate savings using all delivery postcodes pairs and distance from origin to each of postcodes. This is purely based on Clare-Wright Sabing Algorithm
and the calculation check distance from origin to each individual postcode in pair of postcodes and then compare it with distance if these two postcodes are on
same delivery vehicle. Difference between two is saving.
5. Once calculation of saving for each postcode pair is done, the app then run plan_multidrop.py file. the file first does some preparation, but most important.
algorithm is on lines 75 - 451. It goes to each element of saving information, checks if delivery to each of two given postcodes were planned yet,
checks allocate inventory, reduce available inventory, check volume of allocated inventory, add delivery to vehicle, check vehicle capacity. If vehicle is full, 
it unplan this delivery and put inventory back to available, leave delivery in list of unplanned, and check another. Once delivery vehicle is fully planned
with available inventory, it starts next vehicle. It will go back to order, which was left, because did not fit to the vehicle.
6. Result is the plan with only available inventory, all vehicle full (exception may be last one, as there may not be enough to fill it up) and the most important,
the rest is cheapest possible way of delivering, if each mile (kilometre) costs the same.
