package me.vinald.api.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HomeController {
	@GetMapping("/")
	public String home() {
		return "Ecommerce API";
	}

	@GetMapping("/about")
	public String about() {
		return "Ecommerce API - About";
	}
}
