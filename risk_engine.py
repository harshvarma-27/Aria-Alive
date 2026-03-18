def compute_risk(user, pollutants):
    """
    user = {
        "age_group": "child" | "adult" | "senior",
        "conditions": "healthy" | "asthma" | ...
        "outdoor_hours": float
    }
    pollutants = {
        "PM2.5": float, "PM10": float, ...
    }
    """

    # -------------------------------
    # Normalize user data
    # -------------------------------
    age_group = user.get("age_group", "adult")
    condition = user.get("conditions", "healthy")
    hours = float(user.get("outdoor_hours", 1))

    # Age sensitivity
    sensitivity = 1.0
    if age_group in ["child", "senior"]:
        sensitivity += 0.3

    # Health condition sensitivity
    if condition != "healthy":
        sensitivity += 0.5

    # -------------------------------
    # Pollution thresholds (WHO-like)
    # -------------------------------
    thresholds = {
        "PM2.5": 25,
        "PM10": 50,
        "O3": 100,
        "NO2": 40,
        "SO2": 20,
        "CO": 4000
    }

    total_score = 0.0
    worst_pollutant = None
    worst_score = 0.0

    # -------------------------------
    # Risk calculation
    # -------------------------------
    for p, val in pollutants.items():
        val = float(val)  # 🔒 force numeric safety
        limit = thresholds.get(p, 1)

        score = (val / limit) * sensitivity * (hours / 2)
        total_score += score

        if score > worst_score:
            worst_score = score
            worst_pollutant = p

    # -------------------------------
    # Risk category
    # -------------------------------
    if total_score >= 5:
        level = "Severe"
    elif total_score >= 3:
        level = "High"
    elif total_score >= 1.5:
        level = "Moderate"
    else:
        level = "Low"

    return {
        "risk_score": round(total_score, 2),
        "category": level,
        "worst_pollutant": worst_pollutant
    }
