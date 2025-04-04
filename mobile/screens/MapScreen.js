import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  Text,
  Alert,
  Platform,
} from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import Geolocation from '@react-native-community/geolocation';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { API_URL } from '../config';
import Icon from 'react-native-vector-icons/MaterialIcons';

const MapScreen = () => {
  const [region, setRegion] = useState(null);
  const [parkingSpots, setParkingSpots] = useState([]);
  const [isTracking, setIsTracking] = useState(false);
  const [lastSpeed, setLastSpeed] = useState(0);
  const watchId = useRef(null);
  const { token, logout } = useAuth();

  useEffect(() => {
    getCurrentLocation();
    return () => {
      if (watchId.current) {
        Geolocation.clearWatch(watchId.current);
      }
    };
  }, []);

  const getCurrentLocation = () => {
    Geolocation.getCurrentPosition(
      position => {
        const { latitude, longitude } = position.coords;
        setRegion({
          latitude,
          longitude,
          latitudeDelta: 0.01,
          longitudeDelta: 0.01,
        });
        fetchNearbySpots(latitude, longitude);
      },
      error => Alert.alert('Error', error.message),
      { enableHighAccuracy: true }
    );
  };

  const fetchNearbySpots = async (latitude, longitude) => {
    try {
      const response = await axios.get(
        `${API_URL}/nearby-spots?latitude=${latitude}&longitude=${longitude}`,
        {
          headers: { Authorization: token }
        }
      );
      setParkingSpots(response.data);
    } catch (error) {
      console.error('Error al obtener espacios:', error);
    }
  };

  const startDriveTracking = () => {
    setIsTracking(true);
    watchId.current = Geolocation.watchPosition(
      position => {
        const { latitude, longitude, speed } = position.coords;
        setLastSpeed(speed || 0);
        
        // Si la velocidad baja a casi 0 después de estar en movimiento,
        // asumimos que el usuario ha estacionado
        if (lastSpeed > 5 && speed < 1) {
          handleParking(latitude, longitude);
        }
        
        setRegion({
          latitude,
          longitude,
          latitudeDelta: 0.01,
          longitudeDelta: 0.01,
        });
      },
      error => console.error(error),
      {
        enableHighAccuracy: true,
        distanceFilter: 10,
        interval: 1000,
      }
    );
  };

  const stopDriveTracking = () => {
    if (watchId.current) {
      Geolocation.clearWatch(watchId.current);
    }
    setIsTracking(false);
  };

  const handleParking = async (latitude, longitude) => {
    try {
      await axios.post(
        `${API_URL}/parking-event`,
        {
          type: 'parked',
          latitude,
          longitude,
        },
        {
          headers: { Authorization: token }
        }
      );
      stopDriveTracking();
      Alert.alert('¡Estacionado!', 'Se ha registrado tu ubicación de estacionamiento.');
    } catch (error) {
      console.error('Error al registrar estacionamiento:', error);
    }
  };

  const reportSpot = async () => {
    if (!region) return;
    
    try {
      await axios.post(
        `${API_URL}/report-spot`,
        {
          latitude: region.latitude,
          longitude: region.longitude,
        },
        {
          headers: { Authorization: token }
        }
      );
      Alert.alert('Éxito', 'Espacio reportado exitosamente');
      fetchNearbySpots(region.latitude, region.longitude);
    } catch (error) {
      Alert.alert('Error', 'No se pudo reportar el espacio');
    }
  };

  return (
    <View style={styles.container}>
      {region && (
        <MapView
          provider={PROVIDER_GOOGLE}
          style={styles.map}
          region={region}
          showsUserLocation
          showsMyLocationButton
        >
          {parkingSpots.map(spot => (
            <Marker
              key={spot.id}
              coordinate={{
                latitude: spot.latitude,
                longitude: spot.longitude,
              }}
              title={`Espacio disponible`}
              description={`Reportado hace ${Math.round(
                (new Date() - new Date(spot.timestamp)) / 1000 / 60
              )} minutos`}
            />
          ))}
        </MapView>
      )}
      
      <View style={styles.buttonContainer}>
        <TouchableOpacity
          style={[styles.button, isTracking && styles.activeButton]}
          onPress={isTracking ? stopDriveTracking : startDriveTracking}
        >
          <Icon 
            name={isTracking ? "directions-car" : "local-parking"} 
            size={24} 
            color="white" 
          />
          <Text style={styles.buttonText}>
            {isTracking ? 'Detener Seguimiento' : 'Iniciar Búsqueda'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.button} onPress={reportSpot}>
          <Icon name="add-location" size={24} color="white" />
          <Text style={styles.buttonText}>Reportar Espacio</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.logoutButton} onPress={logout}>
          <Icon name="logout" size={24} color="white" />
          <Text style={styles.buttonText}>Cerrar Sesión</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  map: {
    flex: 1,
  },
  buttonContainer: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    flexDirection: 'column',
    gap: 10,
  },
  button: {
    backgroundColor: '#2196F3',
    padding: 15,
    borderRadius: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  activeButton: {
    backgroundColor: '#4CAF50',
  },
  logoutButton: {
    backgroundColor: '#f44336',
    padding: 15,
    borderRadius: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
