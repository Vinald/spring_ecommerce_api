package me.vinald.api.dto;

public record OrderItemResponse(
        Integer productId,
        String productName,
        int quantity,
        double price
) {}
