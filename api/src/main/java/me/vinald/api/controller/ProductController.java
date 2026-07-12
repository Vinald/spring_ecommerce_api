package me.vinald.api.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import me.vinald.api.model.Product;
import me.vinald.api.service.ProductService;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/products")
public class ProductController {
	private final ProductService productService;

	@GetMapping
	public List<Product> getAllProducts() {
		return productService.getAllProducts();
	}

	@GetMapping("/{productId}")
	public Product getProductById(@PathVariable Integer productId) {
		return productService.getProductById(productId);
	}

	@PostMapping
	@ResponseStatus(HttpStatus.CREATED)
	public Product addProduct(@Valid @RequestBody Product product) {
		return productService.addProduct(product);
	}

	@PutMapping("/{productId}")
    public Product updateProduct(@PathVariable Integer productId, @Valid @RequestBody Product product) {
        product.setProductId(productId);
        return productService.updateProduct(product);
    }

    @DeleteMapping("/{productId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteProduct(@PathVariable Integer productId) {
        productService.deleteProduct(productId);
    }

    @GetMapping("/search")
    public List<Product> searchProducts(@RequestParam String search) {
        return productService.searchProduct(search);
    }
}
