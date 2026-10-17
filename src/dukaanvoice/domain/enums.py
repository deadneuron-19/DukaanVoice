from __future__ import annotations

from enum import Enum


class OrderStatus(str, Enum):
    DRAFT = "draft"
    NEEDS_CLARIFICATION = "needs_clarification"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class WorkflowState(str, Enum):
    RECEIVED = "RECEIVED"
    TRANSCRIBED = "TRANSCRIBED"
    EXTRACTED = "EXTRACTED"
    VALIDATING = "VALIDATING"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class Unit(str, Enum):
    KG = "kg"
    G = "g"
    LITRE = "litre"
    ML = "ml"
    PCS = "pcs"
    PACK = "pack"
    BOX = "box"
