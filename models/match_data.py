from pydantic import BaseModel, Field
from typing import List, Optional

class MatchInfo(BaseModel):
    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")
    score: str = Field(..., description="Match score")
    date: str = Field(..., description="Match date")
    competition: str = Field(..., description="Competition/league name")
    venue: Optional[str] = Field(None, description="Stadium/venue name")
    referee: Optional[str] = Field(None, description="Match referee")

class MatchEvent(BaseModel):
    minute: int = Field(..., description="Minute when event occurred")
    period: str = Field(..., description="Match period (first_half, second_half, etc.)")
    event_type: str = Field(..., description="Type of event (goal, card, etc.)")
    description: Optional[str] = Field(None, description="Event details")

class TimelineRating(BaseModel):
    minute: int = Field(..., description="Minute of the timeline snapshot")
    period: str = Field(..., description="Match period")
    ratings: dict = Field(..., description="Player and team ratings at this minute")
    top_performer: Optional[str] = Field(None, description="Top performer at this time")
    top_performer_rating: Optional[float] = Field(None, description="Rating of top performer")
    events_in_period: List[MatchEvent] = Field(default_factory=list, description="Events occurring in this time period")

class PlayerRating(BaseModel):
    player_name: str = Field(..., description="Player full name")
    team: str = Field(..., description="Player's team")
    position: str = Field(..., description="Player position")
    rating: float = Field(..., description="Player rating at this time")
    goals: Optional[int] = Field(None, description="Goals scored")
    assists: Optional[int] = Field(None, description="Assists provided")
    shots: Optional[int] = Field(None, description="Shots taken")
    passes: Optional[int] = Field(None, description="Total passes")
    pass_accuracy: Optional[float] = Field(None, description="Pass accuracy percentage")
    average_rating: float = Field(..., description="Team average rating")

class MatchData(BaseModel):
    match_info: MatchInfo = Field(..., description="Basic match information")
    timeline_ratings: List[TimelineRating] = Field(..., description="Rating progression throughout match")
