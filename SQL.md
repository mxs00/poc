

SELECT metadata_->>'category' AS cat,
       metadata_->>'filename' AS filename,
       metadata_->>'text_as_html' AS text_as_html,
		 metadata_->>'page_number' AS page_number, text FROM data_my_emb_tbl
		 ORDER BY filename,page_number;
