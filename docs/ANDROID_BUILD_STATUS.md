# CardioGuard AI - Android Build Status

## Environment Capability
The current build environment is missing the core Android SDK dependencies required to compile Native Android/WearOS applications.

## Build Failure Output
Running `.\gradlew.bat assembleDebug` inside the `android-native/` directory fails with the following exact error:

```text
FAILURE: Build failed with an exception.

* What went wrong:
Could not determine the dependencies of task ':app:compileDebugJavaWithJavac'.
> SDK location not found. Define a valid SDK location with an ANDROID_HOME environment variable or by setting the sdk.dir path in your project's local properties file at 'D:\cardiogaurd\android-native\local.properties'.
```

## Resolution / Next Steps
To unlock local Android compilation, the following must be provided:
1. Installation of Android Studio / Android Command Line Tools.
2. An `ANDROID_HOME` environment variable mapping to the local SDK path.
3. Acceptance of Android SDK licenses (via `sdkmanager --licenses`).

Until this infrastructure is provisioned, the WearOS app compilation and local TFLite validation remains explicitly **BLOCKED BY ENVIRONMENT**.
