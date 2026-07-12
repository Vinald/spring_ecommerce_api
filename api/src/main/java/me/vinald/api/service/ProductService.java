package me.vinald.api.service;

import lombok.RequiredArgsConstructor;
import me.vinald.api.exceptions.ProductNotFoundException;
import me.vinald.api.model.Product;
import me.vinald.api.repository.ProductRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class ProductService {
	private final ProductRepository productRepository;

	public List<Product> getAllProducts() {
		return productRepository.findAll();
	}

	public Product getProductById(Integer id) {
		return productRepository.findById(id)
				.orElseThrow(() -> new ProductNotFoundException(id));
	}

	public Product addProduct(Product product) {
		return productRepository.save(product);
	}

	public Product updateProduct(Product product) {
		if (!productRepository.existsById(product.getProductId())) {
			throw new ProductNotFoundException(product.getProductId());
		}
		return productRepository.save(product);
	}

	public void deleteProduct(Integer productId) {
		if (!productRepository.existsById(productId)) {
			throw new ProductNotFoundException(productId);
		}
		productRepository.deleteById(productId);
	}
	public List<Product> searchProduct(String search) {
		return productRepository.searchProduct(search);
	}
}
