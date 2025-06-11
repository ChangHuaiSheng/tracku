import 'dart:developer';

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:intl/intl.dart';
import 'package:http/http.dart' as http;
import 'package:tracku/view/loginscreen.dart';

class HomePage extends StatefulWidget {
  final String username;
  final String email;

  const HomePage({super.key, required this.username, required this.email});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  String _location = 'Ready to check in!';
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    // _getLocation();
  }

  Future<void> _getLocation() async {
    setState(() {
      _isLoading = true;
    });

    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) throw 'Location services are disabled.';

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) throw 'Location permissions are denied.';
      }
      if (permission == LocationPermission.deniedForever) {
        throw 'Location permissions are permanently denied.';
      }

      Position position = await Geolocator.getCurrentPosition(desiredAccuracy: LocationAccuracy.high);
      double lat = position.latitude;
      double lng = position.longitude;
      String timestamp = DateFormat("yyyy-MM-dd HH:mm:ss").format(DateTime.now());

      // Send data to the server
      String email = widget.email;
      String url = 'https://muhdhadif.pythonanywhere.com/api/insert_gps_data/$email/$lat/$lng/$timestamp';
      final response = await http.post(Uri.parse(url));

      if (response.statusCode == 200) {
        log('GPS data submitted successfully.');
        setState(() {
          _location = 'Latitude: $lat,\nLongitude: $lng';
          _isLoading = false;
        });
      } else {
        log('Failed to submit GPS data: ${response.statusCode}');
        setState(() {
          _location = 'An error occurred, please try again. (${response.statusCode})';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _location = 'Error: $e';
        _isLoading = false;
      });
    }
  }

  void _logout() {
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => LoginPage()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: Text('TrackU Dashboard', style: TextStyle(color: Colors.deepPurple)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: IconThemeData(color: Colors.deepPurple),
        actions: [
          IconButton(
            onPressed: _logout,
            icon: Icon(Icons.logout),
            tooltip: 'Logout',
          ),
        ],
      ),
      body: Container(
        width: double.infinity,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Colors.deepPurple.shade200, Colors.deepPurple.shade600],
          ),
        ),
        child: Center(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(24, 100, 24, 24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.location_on, size: 90, color: Colors.white),
                SizedBox(height: 10),
                Text(
                  "Hi, ${widget.username.split('@')[0]}!",
                  style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 8),
                Text(
                  "Tap the button below to check in your location.",
                  style: TextStyle(color: Colors.white70, fontSize: 16),
                  textAlign: TextAlign.center,
                ),
                SizedBox(height: 30),
                ElevatedButton.icon(
                  onPressed: _getLocation,
                  icon: Icon(Icons.my_location),
                  label: Text("Check In Now"),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: Colors.deepPurple,
                    padding: EdgeInsets.symmetric(horizontal: 40, vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    textStyle: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    elevation: 6,
                  ),
                ),
                SizedBox(height: 30),
                AnimatedContainer(
                  duration: Duration(milliseconds: 300),
                  padding: EdgeInsets.all(20),
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [BoxShadow(color: Colors.black26, blurRadius: 8)],
                  ),
                  child: _isLoading
                      ? Column(
                          children: [
                            CircularProgressIndicator(color: Colors.deepPurple),
                            SizedBox(height: 10),
                            Text(
                              "Getting location...",
                              style: TextStyle(fontSize: 16, color: Colors.deepPurple.shade700),
                            ),
                          ],
                        )
                      : Text(
                          _location,
                          textAlign: TextAlign.center,
                          style: TextStyle(fontSize: 16, color: Colors.deepPurple.shade700),
                        ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

