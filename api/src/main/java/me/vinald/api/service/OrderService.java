package me.vinald.api.service;

import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import me.vinald.api.dto.OrderItemRequest;
import me.vinald.api.dto.OrderItemResponse;
import me.vinald.api.dto.OrderRequest;
import me.vinald.api.dto.OrderResponse;
import me.vinald.api.exceptions.InsufficientStockException;
import me.vinald.api.exceptions.ProductNotFoundException;
import me.vinald.api.model.Order;
import me.vinald.api.model.OrderItem;
import me.vinald.api.model.Product;
import me.vinald.api.model.User;
import me.vinald.api.repository.OrderRepository;
import me.vinald.api.repository.ProductRepository;
import me.vinald.api.repository.UserRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class OrderService {

    private final OrderRepository orderRepository;
    private final ProductRepository productRepository;
    private final UserRepository userRepository;

    @Transactional
    public OrderResponse createOrder(OrderRequest request, String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED));

        List<OrderItem> items = new ArrayList<>();
        double total = 0;

        for (OrderItemRequest itemReq : request.items()) {
            Product product = productRepository.findById(itemReq.productId())
                    .orElseThrow(() -> new ProductNotFoundException(itemReq.productId()));

            if (product.getQuantity() < itemReq.quantity()) {
                throw new InsufficientStockException(product.getName());
            }

            product.setQuantity(product.getQuantity() - itemReq.quantity());
            productRepository.save(product);

            OrderItem item = new OrderItem();
            item.setProduct(product);
            item.setQuantity(itemReq.quantity());
            item.setPrice(product.getPrice());
            items.add(item);

            total += product.getPrice() * itemReq.quantity();
        }

        Order order = new Order();
        order.setUser(user);
        order.setTotal(total);
        items.forEach(item -> item.setOrder(order));
        order.setItems(items);

        return toResponse(orderRepository.save(order));
    }

    @Transactional(readOnly = true)
    public List<OrderResponse> getUserOrders(String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED));
        return orderRepository.findByUserOrderByCreatedAtDesc(user)
                .stream().map(this::toResponse).toList();
    }

    private OrderResponse toResponse(Order order) {
        List<OrderItemResponse> itemResponses = order.getItems().stream()
                .map(item -> new OrderItemResponse(
                        item.getProduct().getProductId(),
                        item.getProduct().getName(),
                        item.getQuantity(),
                        item.getPrice()
                ))
                .toList();

        return new OrderResponse(
                order.getId(),
                order.getStatus().name(),
                order.getTotal(),
                order.getCreatedAt(),
                itemResponses
        );
    }
}
