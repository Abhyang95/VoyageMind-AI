# VoyageMind AI

### Autonomous Multi-Agent Travel Planning System

VoyageMind AI is an AI-powered travel planning platform that generates personalized travel itineraries using **multi-agent orchestration, LLMs, Retrieval-Augmented Generation (RAG), user memory, machine learning recommendations, real-time external APIs, and PostgreSQL persistence**.

The system combines specialized AI components to handle destination discovery, weather information, place discovery, user preferences, memory retrieval, recommendations, and itinerary generation.

---

## Live Application

**Frontend:**  
https://voyage-mind-ai-cd8x.vercel.app

**Backend API:**  
https://voyagemind-ai-1.onrender.com

---

## Problem Statement

Traditional travel planning requires users to manually search for:

- Destinations
- Places and attractions
- Weather information
- Restaurants
- Activities
- Budget estimates
- Travel preferences
- Daily itineraries

This information is usually distributed across multiple platforms.

VoyageMind AI combines these tasks into a single intelligent travel-planning workflow that understands user preferences and generates personalized trip plans.

---

## Key Features

### AI-Powered Trip Planning

Generate personalized travel itineraries using an LLM-powered planning workflow.

Users can provide:

- Destination
- Departure date
- Return date
- Trip duration
- Budget
- Currency
- Interests
- Walking preference
- Hotel preference
- Restaurant preference

---

### Multi-Agent Architecture

VoyageMind uses a multi-agent workflow to divide travel-planning tasks into specialized components.

The system includes components for:

- Destination discovery
- Weather information
- Place discovery
- User memory retrieval
- AI recommendations
- Itinerary generation

These components contribute information to the final travel-planning workflow.

---

### Real-Time Place Discovery

The Places workflow integrates with external geographic data sources to discover attractions based on selected interests.

Example interests include:

```text
Nature
Shopping
Adventure
Architecture
History
Museums
Nightlife