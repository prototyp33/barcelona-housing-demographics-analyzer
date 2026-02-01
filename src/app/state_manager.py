"""
Global Session State Manager for Barcelona Housing Analytics

Implements the "Global Context" pattern to persist user selections and context
across tabs, solving the User Journey Fragmentation issue.

This module ensures that filters, selections, and user preferences are maintained
consistently throughout the application, creating a cohesive user experience.

Version: 2.3 - Global Context Pattern
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st


# ============================================
# 1. STATE DATA STRUCTURES
# ============================================

@dataclass
class FilterState:
    """Encapsulates all filter selections"""
    selected_district: str = 'All'
    selected_barrio_id: Optional[int] = None
    selected_year: int = 2025
    active_metric: str = 'price_per_sqm'
    date_range: Optional[tuple[datetime, datetime]] = None


@dataclass
class ComparisonState:
    """Manages comparison mode and selected items"""
    compare_mode: bool = False
    comparison_districts: List[str] = field(default_factory=list)
    comparison_barrios: List[int] = field(default_factory=list)
    max_comparisons: int = 4


@dataclass
class ViewState:
    """Tracks current view and navigation state"""
    active_tab: str = 'overview'
    active_subtab: Optional[str] = None
    last_visited_tabs: List[str] = field(default_factory=list)
    max_history: int = 10


@dataclass
class UserPreferences:
    """User preferences and settings"""
    theme: str = 'light'
    chart_height_preference: str = 'standard'  # compact, standard, expanded
    show_advanced_metrics: bool = False
    auto_refresh: bool = False
    language: str = 'es'


@dataclass
class SessionMetadata:
    """Session tracking and analytics"""
    session_id: str = ''
    start_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    page_views: int = 0
    queries_executed: int = 0


# ============================================
# 2. INITIALIZATION FUNCTIONS
# ============================================

def init_session_state() -> None:
    """
    Initialize all session state variables with default values.
    
    This should be called once at the start of the application (in main.py).
    Uses Streamlit's session_state to persist data across reruns.
    """
    # Filter State
    if 'filter_state' not in st.session_state:
        st.session_state.filter_state = FilterState()
    
    # Comparison State
    if 'comparison_state' not in st.session_state:
        st.session_state.comparison_state = ComparisonState()
    
    # View State
    if 'view_state' not in st.session_state:
        st.session_state.view_state = ViewState()
    
    # User Preferences
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = UserPreferences()
    
    # Session Metadata
    if 'session_metadata' not in st.session_state:
        st.session_state.session_metadata = SessionMetadata(
            session_id=_generate_session_id(),
            start_time=datetime.now(),
            last_activity=datetime.now(),
        )
    
    # Legacy compatibility - maintain old keys for backward compatibility
    _init_legacy_state()


def _init_legacy_state() -> None:
    """Initialize legacy session state keys for backward compatibility"""
    legacy_defaults = {
        'selected_district': 'All',
        'selected_year': 2025,
        'active_metric': 'price_per_sqm',
        'compare_mode': False,
        'comparison_districts': [],
        'api_warning_shown': False,
    }
    
    for key, val in legacy_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _generate_session_id() -> str:
    """Generate a unique session ID"""
    import uuid
    return str(uuid.uuid4())[:8]


# ============================================
# 3. FILTER MANAGEMENT
# ============================================

def update_filter_state(
    district: Optional[str] = None,
    barrio_id: Optional[int] = None,
    year: Optional[int] = None,
    metric: Optional[str] = None,
) -> None:
    """
    Update filter state with new values.
    
    Args:
        district: Selected district name or 'All'
        barrio_id: Selected barrio ID
        year: Selected year
        metric: Active metric key
    """
    filter_state: FilterState = st.session_state.filter_state
    
    if district is not None:
        filter_state.selected_district = district
        st.session_state.selected_district = district  # Legacy sync
    
    if barrio_id is not None:
        filter_state.selected_barrio_id = barrio_id
    
    if year is not None:
        filter_state.selected_year = year
        st.session_state.selected_year = year  # Legacy sync
    
    if metric is not None:
        filter_state.active_metric = metric
        st.session_state.active_metric = metric  # Legacy sync
    
    _update_last_activity()


def get_filter_state() -> FilterState:
    """
    Get current filter state.
    
    Returns:
        Current FilterState object
    """
    return st.session_state.filter_state


def reset_filters() -> None:
    """Reset all filters to default values"""
    st.session_state.filter_state = FilterState()
    _init_legacy_state()


# ============================================
# 4. COMPARISON MODE MANAGEMENT
# ============================================

def toggle_comparison_mode() -> None:
    """Toggle comparison mode on/off"""
    comparison_state: ComparisonState = st.session_state.comparison_state
    comparison_state.compare_mode = not comparison_state.compare_mode
    
    # Legacy sync
    st.session_state.compare_mode = comparison_state.compare_mode
    
    # Clear comparisons when turning off
    if not comparison_state.compare_mode:
        comparison_state.comparison_districts = []
        comparison_state.comparison_barrios = []


def add_to_comparison(
    district: Optional[str] = None,
    barrio_id: Optional[int] = None
) -> bool:
    """
    Add an item to comparison list.
    
    Args:
        district: District name to add
        barrio_id: Barrio ID to add
    
    Returns:
        True if added successfully, False if limit reached
    """
    comparison_state: ComparisonState = st.session_state.comparison_state
    
    if district is not None:
        if len(comparison_state.comparison_districts) >= comparison_state.max_comparisons:
            return False
        if district not in comparison_state.comparison_districts:
            comparison_state.comparison_districts.append(district)
            st.session_state.comparison_districts = comparison_state.comparison_districts
    
    if barrio_id is not None:
        if len(comparison_state.comparison_barrios) >= comparison_state.max_comparisons:
            return False
        if barrio_id not in comparison_state.comparison_barrios:
            comparison_state.comparison_barrios.append(barrio_id)
    
    return True


def remove_from_comparison(
    district: Optional[str] = None,
    barrio_id: Optional[int] = None
) -> None:
    """
    Remove an item from comparison list.
    
    Args:
        district: District name to remove
        barrio_id: Barrio ID to remove
    """
    comparison_state: ComparisonState = st.session_state.comparison_state
    
    if district is not None and district in comparison_state.comparison_districts:
        comparison_state.comparison_districts.remove(district)
        st.session_state.comparison_districts = comparison_state.comparison_districts
    
    if barrio_id is not None and barrio_id in comparison_state.comparison_barrios:
        comparison_state.comparison_barrios.remove(barrio_id)


def get_comparison_state() -> ComparisonState:
    """Get current comparison state"""
    return st.session_state.comparison_state


# ============================================
# 5. VIEW/NAVIGATION MANAGEMENT
# ============================================

def update_active_view(tab: str, subtab: Optional[str] = None) -> None:
    """
    Update the active view/tab.
    
    Args:
        tab: Main tab name
        subtab: Optional subtab name
    """
    view_state: ViewState = st.session_state.view_state
    
    # Update active tab
    view_state.active_tab = tab
    view_state.active_subtab = subtab
    
    # Add to history
    if tab not in view_state.last_visited_tabs:
        view_state.last_visited_tabs.append(tab)
        
        # Maintain max history size
        if len(view_state.last_visited_tabs) > view_state.max_history:
            view_state.last_visited_tabs.pop(0)
    
    _update_last_activity()


def get_view_state() -> ViewState:
    """Get current view state"""
    return st.session_state.view_state


def get_navigation_history() -> List[str]:
    """Get list of recently visited tabs"""
    return st.session_state.view_state.last_visited_tabs


# ============================================
# 6. USER PREFERENCES
# ============================================

def update_user_preference(key: str, value: Any) -> None:
    """
    Update a user preference.
    
    Args:
        key: Preference key (must be a field in UserPreferences)
        value: New value
    """
    preferences: UserPreferences = st.session_state.user_preferences
    
    if hasattr(preferences, key):
        setattr(preferences, key, value)


def get_user_preference(key: str, default: Any = None) -> Any:
    """
    Get a user preference value.
    
    Args:
        key: Preference key
        default: Default value if key doesn't exist
    
    Returns:
        Preference value or default
    """
    preferences: UserPreferences = st.session_state.user_preferences
    return getattr(preferences, key, default)


def get_user_preferences() -> UserPreferences:
    """Get all user preferences"""
    return st.session_state.user_preferences


# ============================================
# 7. SESSION ANALYTICS
# ============================================

def increment_page_view() -> None:
    """Increment page view counter"""
    metadata: SessionMetadata = st.session_state.session_metadata
    metadata.page_views += 1
    _update_last_activity()


def increment_query_count() -> None:
    """Increment query execution counter"""
    metadata: SessionMetadata = st.session_state.session_metadata
    metadata.queries_executed += 1
    _update_last_activity()


def get_session_metadata() -> SessionMetadata:
    """Get session metadata"""
    return st.session_state.session_metadata


def get_session_duration() -> Optional[float]:
    """
    Get session duration in seconds.
    
    Returns:
        Duration in seconds or None if session not started
    """
    metadata: SessionMetadata = st.session_state.session_metadata
    
    if metadata.start_time is None:
        return None
    
    return (datetime.now() - metadata.start_time).total_seconds()


def _update_last_activity() -> None:
    """Update last activity timestamp"""
    metadata: SessionMetadata = st.session_state.session_metadata
    metadata.last_activity = datetime.now()


# ============================================
# 8. CONTEXT SYNCHRONIZATION
# ============================================

def sync_filters_to_widgets() -> Dict[str, Any]:
    """
    Synchronize filter state to widget values.
    
    Returns:
        Dictionary of widget values to use in st.selectbox, st.slider, etc.
    """
    filter_state = get_filter_state()
    
    return {
        'district': filter_state.selected_district,
        'barrio_id': filter_state.selected_barrio_id,
        'year': filter_state.selected_year,
        'metric': filter_state.active_metric,
    }


def sync_widgets_to_filters(
    district: Optional[str] = None,
    barrio_id: Optional[int] = None,
    year: Optional[int] = None,
    metric: Optional[str] = None,
) -> None:
    """
    Synchronize widget values back to filter state.
    
    This should be called after widget interactions to ensure state consistency.
    
    Args:
        district: Value from district selectbox
        barrio_id: Value from barrio selectbox
        year: Value from year slider
        metric: Value from metric selectbox
    """
    update_filter_state(
        district=district,
        barrio_id=barrio_id,
        year=year,
        metric=metric,
    )


# ============================================
# 9. UTILITY FUNCTIONS
# ============================================

def get_full_context() -> Dict[str, Any]:
    """
    Get complete application context as a dictionary.
    
    Useful for debugging or passing context to functions.
    
    Returns:
        Dictionary containing all state objects
    """
    return {
        'filters': get_filter_state(),
        'comparison': get_comparison_state(),
        'view': get_view_state(),
        'preferences': get_user_preferences(),
        'metadata': get_session_metadata(),
    }


def export_session_state() -> Dict[str, Any]:
    """
    Export session state for persistence or debugging.
    
    Returns:
        Serializable dictionary of session state
    """
    from dataclasses import asdict
    
    context = get_full_context()
    
    return {
        'filters': asdict(context['filters']),
        'comparison': asdict(context['comparison']),
        'view': asdict(context['view']),
        'preferences': asdict(context['preferences']),
        'metadata': {
            **asdict(context['metadata']),
            'start_time': context['metadata'].start_time.isoformat() if context['metadata'].start_time else None,
            'last_activity': context['metadata'].last_activity.isoformat() if context['metadata'].last_activity else None,
        }
    }


def clear_all_state() -> None:
    """Clear all session state (use with caution!)"""
    keys_to_clear = [
        'filter_state',
        'comparison_state',
        'view_state',
        'user_preferences',
        'session_metadata',
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Reinitialize
    init_session_state()
