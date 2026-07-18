package me.vinald.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record OrderItemRequest(
        @NotNull(message = "Product ID is required")
        Integer productId,

        @Positive(message = "Quantity must be at least 1")
        int quantity
) {}
