package me.vinald.api.repository;

import me.vinald.api.model.Product;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface ProductRepository extends JpaRepository<Product, Integer> {
	@Query("SELECT p FROM Product p WHERE LOWER(p.name) " +
			"LIKE LOWER(CONCAT('%', :search, '%')) " +
			"OR LOWER(p.description) LIKE LOWER(CONCAT('%', :search, '%')) " +
			"OR LOWER(p.category) LIKE LOWER(CONCAT('%', :search, '%'))")
	List<Product> searchProduct(@Param("search") String search);
}
