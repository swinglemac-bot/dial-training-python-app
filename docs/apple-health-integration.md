# Apple Health Integration

Dialed is now prepared to read Apple Health data through a native iOS bridge named `DialedHealthKit`.

## App-side bridge contract

The React Native app expects a native module with this shape:

```ts
type DialedHealthKitModule = {
  requestAuthorization(): Promise<boolean>;
  getTodayHealthSnapshot(): Promise<{
    source?: string;
    steps?: number;
    durationMinutes?: number;
    caloriesBurned?: number;
    activeEnergyBurned?: number;
    averageHeartRate?: number;
    maxHeartRate?: number;
    restingHeartRate?: number;
    heartRateVariability?: number;
    sleepHours?: number;
    recoveryScore?: number;
    syncedAt?: string;
  }>;
};
```

The app-side wrapper lives in [healthKitBridge.ts](C:/temp/Swingle%20Backup/projects/dialed/healthKitBridge.ts).

## Where the data is used

- [screens/WorkoutSummaryScreen.tsx](C:/temp/Swingle%20Backup/projects/dialed/screens/WorkoutSummaryScreen.tsx)
  - `Pull Apple Health Snapshot`
  - saves imported metrics with the workout
- [screens/ResultsScreen.tsx](C:/temp/Swingle%20Backup/projects/dialed/screens/ResultsScreen.tsx)
  - shows expanded wearable metrics
  - includes the metrics in coach analysis
- [screens/ConnectedDevicesScreen.tsx](C:/temp/Swingle%20Backup/projects/dialed/screens/ConnectedDevicesScreen.tsx)
  - shows whether the native Apple Health bridge is installed

## Current supported metrics

- steps
- duration minutes
- calories burned
- active energy burned
- average heart rate
- max heart rate
- resting heart rate
- heart rate variability
- sleep hours
- recovery score

## Native implementation direction

The sample app in [native-ios/HealthStepsDemo](C:/temp/Swingle%20Backup/projects/dialed/native-ios/HealthStepsDemo) already contains HealthKit query logic for:

- step count
- average heart rate
- sleep

The next native iOS step is to wrap that logic in a React Native / Expo-compatible native module named `DialedHealthKit`, then expose `requestAuthorization` and `getTodayHealthSnapshot` to the JS app.
