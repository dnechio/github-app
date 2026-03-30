package com.middleware.model;

import java.time.LocalDateTime;

public class CameraReading {

    private final String cameraName;
    private final String rawData;
    private final String readCode;
    private final boolean success;
    private final LocalDateTime timestamp;

    public CameraReading(String cameraName, String rawData, String readCode, boolean success) {
        this.cameraName = cameraName;
        this.rawData = rawData;
        this.readCode = readCode;
        this.success = success;
        this.timestamp = LocalDateTime.now();
    }

    public String getCameraName() { return cameraName; }
    public String getRawData()    { return rawData; }
    public String getReadCode()   { return readCode; }
    public boolean isSuccess()    { return success; }
    public LocalDateTime getTimestamp() { return timestamp; }

    @Override
    public String toString() {
        return "CameraReading{" +
                "camera='" + cameraName + '\'' +
                ", code='" + readCode + '\'' +
                ", success=" + success +
                ", timestamp=" + timestamp +
                '}';
    }
}
