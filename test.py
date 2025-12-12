x = {
  "cameraID": 1,
  "timeWindow": {
    "start": "2025-11-06T14:30:45",
    "end": "2025-11-06T14:35:45",
    "totalFrames": 300
  },

  "objects": [
    {
      "className": 0,


      # GENEL PRESENCE
      "cameraPresence": {
        "firstDetection": "14:30:45",
        "lastDetection": "14:35:42",
        "totalDetectedFrames": 150,
        "maxCount": 5,
        "minCount": 0,
        "detectionRate": 0.50, # 150/300
        "avgConfidence": 83.2, # bu hangi insanın ortalama confidencesi olabilir ki?
        "stateTransitions": [ # burası hep 5
          {
            "min": 1,
            "count": 5,
            "status": "IN_CAMERA_NO_REGION",
            "region": []
          },
          {
            "min": 2,
            "count": 3,
            "status": "IN_REGION",
            "region": [1]
          },
          {
            "min": 3,
            "count": 5,
            "status": "IN_REGION",
            "region": [1,2]
          },
          {
            "min": 4,
            "count": 0,
            "status": "IN_CAMERA_NO_REGION",
            "region": []
          },
          {
            "min": 5,
            "count": 0,
            "status": "IN_CAMERA_NO_REGION",
            "region": []
          }
        ]
      },

      # REGION BAZLI DETAY
      "regionActivity": {
        "outsideAllRegions": {
          "totalFrames": 100,
          "duration": "1m40s",
          "percentage": 66.7, # 100/150 (sadece tespit edilen framelerden)
          "periods": [
            {
              "start": "14:30:45",
              "end": "14:33:45",
              "frameCount": 100,
            }
          ]
        },

        "regions": [
          {
            "regionID": 1,
            "totalFrames": 50,
            "duration": "50s",
            "percentage": 33.3, # 50/150
            "entries": 1,
            "exits": 0, # hala içinde
            "periods": [
              {
                "entryTime": "14:33:45",
                "exitTime": None, # hala içinde
                "frameCount": 50,
                "avgConfidence": 82.8,
                "avgPosition": { "x": 380, "y": 520 },
                "dwellTime": "50s"
              }
            ]
          }
        ]
      },

      # AI TESPİT GÜVENİLİRLİĞİ
      "detectionQuality": {
        "notDetectedFrames": 150,
        "detectedFrames": 150,
        "longestGap": {
          "duration": "25s",
          "frameCount": 25,
          "startFrame": 60,
          "endFrame": 85,
          "beforeState": "IN_CAMERA_NO_REGION",
          "afterState": "IN_CAMERA_NO_REGION",
          "likelyPresent": True # interpolation sonucu
        },
        "gapAnalysis": {
          "totalGaps": 8,
          "avgGapDuration": "5s",
          "interpolatedPresence": True # boşlukları doldur
        }
      }
    }
  ],

  # KAMERA SEVİYESİNDE ÖZET
  "cameraSummary": {
    "totalUniqueObjects": 1,
    "regionTraffic": {
      "1": { "entries": 1, "uniqueObjects": 1, "avgDwellTime": "50s" }
    }
  },
  "payload": [
    {
      "cameraID": 1,
      "eventDate": "2025-11-06T14:30:45.123456",
      "detectedObjects": [
        {
          "className": 0,
          "confidence": 85,
          "photoUrl": "kapi_saved_images/person_85_1730901045.jpg",
          "coordinateX": 450,
          "coordinateY": 320,
          "regionID": []
        },
        {
          "className": 0,
          "confidence": 92,
          "photoUrl": "kapi_saved_images/person_92_1730901045.jpg",
          "coordinateX": 120,
          "coordinateY": 580,
          "regionID": [2]
        },
        {
          "className": 0,
          "confidence": 90,
          "photoUrl": "kapi_saved_images/person_92_17309012135.jpg",
          "coordinateX": 10,
          "coordinateY": 50,
          "regionID": []
        }
      ]
    },
    {
      "cameraID": 1,
      "eventDate": "2025-11-06T15:02:18.456789",
      "detectedObjects": [
        {
          "className": 0,
          "confidence": 78,
          "photoUrl": "depo_saved_images/person_78_1730904138.jpg",
          "coordinateX": 230,
          "coordinateY": 410,
          "regionID": [4]
        }
      ]
    },
    {
      "cameraID": 1,
      "eventDate": "2025-11-07T09:15:03.234567",
      "detectedObjects": [
        {
          "className": 0,
          "confidence": 96,
          "photoUrl": "park_saved_images/person_96_1730954103.jpg",
          "coordinateX": 800,
          "coordinateY": 240,
          "regionID": [5, 6]
        },
        {
          "className": 0,
          "confidence": 88,
          "photoUrl": "park_saved_images/person_88_1730954103.jpg",
          "coordinateX": 200,
          "coordinateY": 700,
          "regionID": []
        }
      ]
    }
  ]
}

exampleStreamData = [
  {
    "cameraID": 1,
    "eventDate": "2025-11-06T14:30:45.123456",
    "detectedObjects": [
      {
        "className": 0,
        "confidence": 85,
        "photoUrl": "kapi_saved_images/person_85_1730901045.jpg",
        "coordinateX": 450,
        "coordinateY": 320,
        "regionID": [1, 3]
      },
      {
        "className": 0,
        "confidence": 92,
        "photoUrl": "kapi_saved_images/person_92_1730901045.jpg",
        "coordinateX": 120,
        "coordinateY": 580,
        "regionID": [2]
      },
      {
        "className": 3,
        "confidence": 90,
        "photoUrl": "kapi_saved_images/car_92_17309012135.jpg",
        "coordinateX": 10,
        "coordinateY": 50,
        "regionID": []
      }
    ]
  },
  {
    "cameraID": 1,
    "eventDate": "2025-11-06T15:02:18.456789",
    "detectedObjects": [
      {
        "className": 1,
        "confidence": 78,
        "photoUrl": "depo_saved_images/person_78_1730904138.jpg",
        "coordinateX": 230,
        "coordinateY": 410,
        "regionID": [4]
      }
    ]
  },
  {
    "cameraID": 1,
    "eventDate": "2025-11-07T09:15:03.234567",
    "detectedObjects": [
      {
        "className": 2,
        "confidence": 96,
        "photoUrl": "park_saved_images/car_96_1730954103.jpg",
        "coordinateX": 800,
        "coordinateY": 240,
        "regionID": [5, 6]
      },
      {
        "className": 2,
        "confidence": 88,
        "photoUrl": "park_saved_images/bike_88_1730954103.jpg",
        "coordinateX": 200,
        "coordinateY": 700,
        "regionID": []
      }
    ]
  },
  {
    "cameraID": 1,
    "eventDate": "2025-11-07T12:47:59.987654",
    "detectedObjects": [
      {
        "className": 0,
        "confidence": 82,
        "photoUrl": "giris_saved_images/person_82_1730966879.jpg",
        "coordinateX": 380,
        "coordinateY": 520,
        "regionID": [1, 7]
      }
    ]
  },
  {
    "cameraID": 1,
    "eventDate": "2025-11-08T06:33:22.654321",
    "detectedObjects": [
      {
        "className": 3,
        "confidence": 91,
        "photoUrl": "arka_saved_images/truck_91_1731030802.jpg",
        "coordinateX": 650,
        "coordinateY": 150,
        "regionID": [8]
      },
      {
        "className": 0,
        "confidence": 73,
        "photoUrl": "arka_saved_images/person_73_1731030802.jpg",
        "coordinateX": 200,
        "coordinateY": 320,
        "regionID": [8, 9]
      }
    ]
  },
  {
    "cameraID": 1,
    "eventDate": "2025-11-08T21:10:14.345678",
    "detectedObjects": [
      {
        "className": 5,
        "confidence": 80,
        "photoUrl": "otopark_saved_images/dog_80_1731078614.jpg",
        "coordinateX": 110,
        "coordinateY": 400,
        "regionID": []
      }
    ]
  },
  {
    "cameraID": 1,
    "eventDate": "2025-11-09T07:25:31.678901",
    "detectedObjects": []
  },
  {
    "cameraID": 1,
    "eventDate": "2025-11-09T18:42:50.111111",
    "detectedObjects": [
      {
        "className": 2,
        "confidence": 79,
        "photoUrl": "cadde_saved_images/car_79_1731157370.jpg",
        "coordinateX": 720,
        "coordinateY": 300,
        "regionID": [11, 12]
      }
    ]
  },
  {
    "cameraID": 1,
    "eventDate": "2025-11-10T03:56:12.222222",
    "detectedObjects": [
      {
        "className": 0,
        "confidence": 88,
        "photoUrl": "arka_giris_saved_images/person_88_1731188172.jpg",
        "coordinateX": 500,
        "coordinateY": 430,
        "regionID": []
      },
      {
        "className": 3,
        "confidence": 92,
        "photoUrl": "arka_giris_saved_images/van_92_1731188172.jpg",
        "coordinateX": 800,
        "coordinateY": 120,
        "regionID": [13]
      }
    ]
  },
  {
    "cameraID": 1,
    "eventDate": "2025-11-10T16:11:41.999999",
    "detectedObjects": [
      {
        "className": 7,
        "confidence": 89,
        "photoUrl": "ofis_saved_images/fire_extinguisher_89_1731226301.jpg",
        "coordinateX": 60,
        "coordinateY": 85,
        "regionID": []
      },
      {
        "className": 0,
        "confidence": 83,
        "photoUrl": "ofis_saved_images/person_83_1731226301.jpg",
        "coordinateX": 140,
        "coordinateY": 400,
        "regionID": [14, 15]
      }
    ]
  }
]

y= {
    "cameraID": 1,
    "timeWindow": {
        "start": "2025-11-06T14:30:00",
        "end": "2025-11-06T14:35:00",
        "totalFrames": 300,
        "framesWithDetection": 287
    },

    "classSummary": {
        "0": {  # person
        "totalDetections": 620,
        "maxInFrame": 4,
        "minInFrame": 0,
        "avgPerFrame": 2.16,
        "framesPresent": 285,
        "avgConfidence": 84.3
},
"2": {  # car
"totalDetections": 142,
"maxInFrame": 2,
"minInFrame": 0,
"avgPerFrame": 0.49,
"framesPresent": 98,
"avgConfidence": 87.5
}
},

"regionSummary": {
    "1": {
        "totalDetections": 195,
        "classCounts": {
            "0": {
                "maxInFrame": 3,
                "minInFrame": 0,
                "avgPerFrame": 0.65,
                "framesPresent": 142,
},
        },
        "avgConfidence": 85.1,
        "activityType": "high_traffic"  # low_traffic, stationary, transient
},
}
}