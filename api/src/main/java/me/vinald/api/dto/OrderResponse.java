package me.vinald.api.dto;

import java.time.LocalDateTime;
import java.util.List;

public record OrderResponse(
		Long id,
		String status,
		double total,
		LocalDateTime createdAt,
		List<OrderItemResponse> items
) {
}
