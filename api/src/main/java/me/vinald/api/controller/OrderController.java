package me.vinald.api.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import me.vinald.api.dto.OrderRequest;
import me.vinald.api.dto.OrderResponse;
import me.vinald.api.service.OrderService;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("api/orders")
@RequiredArgsConstructor
public class OrderController {

	private final OrderService orderService;

	@PostMapping
	@ResponseStatus(HttpStatus.CREATED)
	public OrderResponse createOrder(@Valid @RequestBody OrderRequest orderRequest, @AuthenticationPrincipal UserDetails userDetails) {
		return orderService.createOrder(orderRequest, userDetails.getUsername());
	}

	@GetMapping
	public List<OrderResponse> getMyOrders(@AuthenticationPrincipal UserDetails userDetails) {
		return orderService.getUserOrders(userDetails.getUsername());
	}

}
